import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const makeRequest = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// Cache storage
const cache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Request deduplication
const pendingRequests = new Map();

const useQuery = (url, options = {}) => {
    const {
        method = 'GET',
        body = null,
        enabled = true,
        cacheTime = CACHE_DURATION,
        staleTime = 2 * 60 * 1000, // 默认 2 分钟内不重新请求
        refetchOnMount = false, // 默认不重新获取，使用缓存
    } = options;

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const cacheKeyRef = useRef(null);
    const abortControllerRef = useRef(null);
    const isMountedRef = useRef(true);

    useEffect(() => {
        isMountedRef.current = true;
        
        if (!url || !enabled) {
            setData(null);
            setLoading(false);
            return;
        }

        // Generate cache key
        const cacheKey = `${method}:${url}:${body ? JSON.stringify(body) : ''}`;
        cacheKeyRef.current = cacheKey;

        // Check cache
        const cached = cache.get(cacheKey);
        const now = Date.now();
        const cacheAge = cached ? (now - cached.timestamp) : Infinity;

        // 如果缓存中的数据为 null 或 undefined，说明之前的请求可能被取消了，需要重新 fetch
        const hasValidCache = cached && cacheAge < cacheTime && cached.data != null;

        if (hasValidCache) {
            // Use cached data immediately
            setData(cached.data);
            setLoading(false);
            setError(null);

            // Check if data is stale
            const isStale = staleTime > 0 && cacheAge > staleTime;

            if (isStale) {
                // Data is stale, revalidate in background (don't show loading)
                fetchData(false);
            } else if (!refetchOnMount) {
                // Data is fresh and refetchOnMount is false, just use cache
                return;
            } else {
                // refetchOnMount is true, but data is fresh, still use cache but check for updates
                // Only refetch if explicitly requested
                fetchData(false); // Background refetch without showing loading
            }
        } else {
            // No cache, cache expired, or cache data is null (request was aborted)
            // Clear invalid cache
            if (cached && cached.data == null) {
                cache.delete(cacheKey);
            }
            // Fetch data
            fetchData(true);
        }

        return () => {
            isMountedRef.current = false;
            
            // 如果请求还在进行中（pendingRequests 中有该请求），清除缓存
            // 这样重新挂载时会重新 fetch
            if (cacheKeyRef.current && pendingRequests.has(cacheKeyRef.current)) {
                // 请求还在进行中，清除缓存以确保重新挂载时会重新 fetch
                cache.delete(cacheKeyRef.current);
            }
            
            // Cancel request on unmount
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [url, method, body, enabled, cacheTime, staleTime, refetchOnMount]);

    const fetchData = async (showLoading = true) => {
        const cacheKey = cacheKeyRef.current;
        
        // Check if request is already pending
        if (pendingRequests.has(cacheKey)) {
            // Wait for pending request
            try {
                const pendingData = await pendingRequests.get(cacheKey);
                setData(pendingData);
                setLoading(false);
                setError(null);
            } catch (err) {
                setError(err);
                setLoading(false);
            }
            return;
        }

        // Create abort controller
        abortControllerRef.current = new AbortController();

        // Create request promise
        const requestPromise = (async () => {
            try {
                if (showLoading) {
                    setLoading(true);
                }
                setError(null);

                const res = await (method === 'GET' 
                    ? makeRequest.get(url, { signal: abortControllerRef.current.signal })
                    : makeRequest.post(url, body, { signal: abortControllerRef.current.signal }));

                // API 返回格式可能是：
                // 1. { status: "success", data: {...} } - 新格式（如 /api/reviews/search）
                // 2. { status: "needs_mining", ... } - 需要 mining 的状态
                // 3. { data: {...} } - 旧格式（如 /airlines/{airline}/kpis）
                // 4. {...} - 直接返回数据
                let responseData;
                if (res.data && res.data.status === 'success' && res.data.data) {
                    // 新格式：{ status: "success", data: {...} }
                    responseData = res.data.data;
                } else if (res.data && res.data.status === 'needs_mining') {
                    // 需要 mining 的状态，保持完整响应以便前端处理
                    responseData = res.data;
                } else if (res.data && res.data.data && !res.data.status) {
                    // 旧格式：{ data: {...} }
                    responseData = res.data.data;
                } else {
                    // 直接返回数据或保持原格式
                    responseData = res.data;
                }

                // Cache the response only if not aborted
                if (!abortControllerRef.current.signal.aborted && isMountedRef.current) {
                    cache.set(cacheKey, {
                        data: responseData,
                        timestamp: Date.now()
                    });

                    setData(responseData);
                    setLoading(false);
                }

                // Remove from pending requests
                pendingRequests.delete(cacheKey);

                return responseData;
            } catch (err) {
                // Remove from pending requests
                pendingRequests.delete(cacheKey);

                // 如果请求被取消（组件卸载），清除缓存，这样重新挂载时会重新 fetch
                if (err.name === 'CanceledError' || abortControllerRef.current.signal.aborted) {
                    // 清除缓存，确保重新挂载时会重新 fetch
                    cache.delete(cacheKey);
                    if (isMountedRef.current) {
                        setLoading(false);
                    }
                } else if (isMountedRef.current) {
                    setError(err);
                    setLoading(false);
                    if (err.response?.status !== 404) {
                        toast.error(err.message || 'Request failed');
                    }
                }
                throw err;
            }
        })();

        // Store pending request
        pendingRequests.set(cacheKey, requestPromise);

        return requestPromise;
    };

    const refetch = () => {
        // Clear cache and refetch
        if (cacheKeyRef.current) {
            cache.delete(cacheKeyRef.current);
        }
        fetchData(true);
    };

    return { data, loading, error, refetch };
};

export default useQuery;

