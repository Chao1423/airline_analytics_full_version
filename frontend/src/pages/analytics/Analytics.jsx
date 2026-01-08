import React, { useState, useMemo, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import useQuery from "../../hooks/useQuery";
import useContext from "../../zustand/useContext";
import axios from "axios";
import { TrendingUp, TrendingDown, ArrowUp, ArrowDown, AlertCircle } from "lucide-react";
import { AirSightDialog } from "../../components/RAG/AirSightDialog";

const makeRequest = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

const Analytics = () => {
    const targetAirline = useContext((state) => state.targetAirline);
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [sortBy, setSortBy] = useState('coef'); // 'coef', 'p_value', 'topic_id'
    const [selectedTopic, setSelectedTopic] = useState(null);
    const [showSimulator, setShowSimulator] = useState(false);
    
    // 模拟器状态（固定为 Drivers 面板的值）
    const [selectedTopics, setSelectedTopics] = useState([]); // [{topic_id, topic_label, coef, share_change_pct}, ...]
    const [simulationResult, setSimulationResult] = useState(null);
    const [simulating, setSimulating] = useState(false);
    
    // Simulator 的输入字段固定为 Drivers 面板的值
    const simulatorAirline = targetAirline || '';
    const simulatorStartDate = startDate;
    const simulatorEndDate = endDate;
    
    // Topic mining 状态
    const [miningStatus, setMiningStatus] = useState(null); // null, 'mining', 'success', 'error'
    const [miningMessage, setMiningMessage] = useState('');
    
    // 构建 Drivers API URL
    const driversUrl = useMemo(() => {
        if (!targetAirline) return null;
        const params = new URLSearchParams({ compute: 'false', auto_mine: 'true' });
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        return `/api/airlines/${encodeURIComponent(targetAirline)}/drivers?${params.toString()}`;
    }, [targetAirline, startDate, endDate]);
    
    const { data: driversData, loading: driversLoading, refetch: refetchDrivers } = useQuery(driversUrl, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });
    
    // 运行 topic mining
    const runTopicMining = useCallback(async () => {
        if (!targetAirline) return;
        
        setMiningStatus('mining');
        setMiningMessage('Executing topic mining, please wait...');
        
        try {
            const response = await makeRequest.post('/api/topic-mining/run', {
                airline_name: targetAirline,
                start_date: startDate || null,
                end_date: endDate || null,
                sentiment: 'both',
                min_topic_size: 10
            });
            
            if (response.data.status === 'success') {
                setMiningStatus('success');
                setMiningMessage('Topic mining completed! Refreshing data...');
                
                // 等待一下让数据写入完成
                setTimeout(() => {
                    // 重新获取 drivers 数据
                    refetchDrivers();
                    setMiningStatus(null);
                    setMiningMessage('');
                }, 2000);
            }
        } catch (error) {
            setMiningStatus('error');
            setMiningMessage('Topic mining failed: ' + (error.response?.data?.detail || error.message));
            console.error('Error running topic mining:', error);
        }
    }, [targetAirline, startDate, endDate, refetchDrivers]);
    
    // 检查是否需要运行 topic mining
    useEffect(() => {
        if (driversData && driversData.status === 'needs_mining' && !miningStatus) {
            // 需要运行 topic mining
            runTopicMining();
        }
    }, [driversData, miningStatus, runTopicMining]);
    
    // 获取代表性评论（点击 topic 时）
    const [representativeReviews, setRepresentativeReviews] = useState([]);
    const [loadingReviews, setLoadingReviews] = useState(false);
    
    const handleTopicClick = async (topicId) => {
        setSelectedTopic(topicId);
        setLoadingReviews(true);
        
        try {
            const params = new URLSearchParams({
                airline_name: targetAirline,
                topic_id: topicId.toString(),
                page: '1',
                page_size: '5'
            });
            const response = await makeRequest.get(`/api/reviews/search?${params.toString()}`);
            const reviews = response.data?.data?.reviews || [];
            setRepresentativeReviews(reviews);
        } catch (error) {
            console.error('Error fetching representative reviews:', error);
            setRepresentativeReviews([]);
        } finally {
            setLoadingReviews(false);
        }
    };
    
    // 处理模拟
    const handleSimulate = async () => {
        if (!simulatorAirline || selectedTopics.length === 0) {
            alert('Please select an airline and at least one topic');
            return;
        }
        
        setSimulating(true);
        try {
            const response = await makeRequest.post('/api/simulate', {
                airline_name: simulatorAirline,
                start_date: simulatorStartDate || null,
                end_date: simulatorEndDate || null,
                topic_changes: selectedTopics.map(t => ({
                    topic_id: t.topic_id,
                    share_change_pct: t.share_change_pct // -50 到 +50
                }))
            });
            
            setSimulationResult(response.data?.data || null);
        } catch (error) {
            console.error('Error simulating:', error);
            alert('Simulation failed: ' + (error.response?.data?.detail || error.message));
        } finally {
            setSimulating(false);
        }
    };
    
    // 处理添加 topic 到模拟器
    const handleAddTopicToSimulator = (topic) => {
        if (selectedTopics.length >= 3) {
            alert('Maximum 3 topics allowed');
            return;
        }
        
        // 使用 topic_label 来检查是否已添加（因为多个 topics 可能有相同的 topic_id）
        if (selectedTopics.find(t => t.topic_label === topic.topic_label)) {
            alert('Topic already added');
            return;
        }
        
        // 根据 topic 的 coef 设置默认值
        // negative topics: 默认减少 10% (share_change_pct = -10)
        // positive topics: 默认增加 10% (share_change_pct = +10)
        const defaultChange = topic.coef < 0 ? -10 : 10;
        
        setSelectedTopics([...selectedTopics, {
            topic_id: topic.topic_id,
            topic_label: topic.topic_label,
            coef: topic.coef,
            share_change_pct: defaultChange // -50 到 +50，负数表示减少，正数表示增加
        }]);
        
        // 显示成功提示
        alert(`Topic "${topic.topic_label || `Topic ${topic.topic_id}`}" added to simulator!`);
    };
    
    // 处理更新 topic 的 share_change_pct
    const handleUpdateTopicChange = (topicLabel, changePct) => {
        setSelectedTopics(selectedTopics.map(t => 
            t.topic_label === topicLabel 
                ? { ...t, share_change_pct: changePct }
                : t
        ));
    };
    
    // 处理移除 topic
    const handleRemoveTopic = (topicLabel) => {
        setSelectedTopics(selectedTopics.filter(t => t.topic_label !== topicLabel));
    };
    
    // 处理排序
    const sortedTopics = useMemo(() => {
        // 处理不同的数据格式：可能是 { status: 'success', data: {...} } 或直接是 { topics: [...] }
        const actualData = driversData?.status === 'success' ? driversData.data : driversData;
        if (!actualData?.topics) return [];
        const topics = [...actualData.topics];
        
        if (sortBy === 'coef') {
            topics.sort((a, b) => Math.abs(b.coef) - Math.abs(a.coef));
        } else if (sortBy === 'p_value') {
            topics.sort((a, b) => a.p_value - b.p_value);
        } else if (sortBy === 'topic_id') {
            topics.sort((a, b) => a.topic_id - b.topic_id);
        }
        
        return topics;
    }, [driversData, sortBy]);
    
    // 分离正向和负向 topics
    const positiveTopics = useMemo(() => sortedTopics.filter(t => t.coef > 0), [sortedTopics]);
    const negativeTopics = useMemo(() => sortedTopics.filter(t => t.coef < 0), [sortedTopics]);
    
    return (
        <div className="flex gap-4 p-4">
            {/* 左侧：Drivers 和 Simulator */}
            <div className="flex-1 flex flex-col gap-4">
                {/* Drivers 面板 */}
                <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80]">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-xl font-semibold">Topic Drivers Analysis</CardTitle>
                        <div className="flex gap-2 items-center">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setShowSimulator(!showSimulator)}
                            >
                                {showSimulator ? 'Hide' : 'Show'} Simulator
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => refetchDrivers()}
                            >
                                Refresh
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* 筛选条件 */}
                    <div className="flex gap-4 items-end">
                        <div className="flex-1">
                            <Label className="text-sm font-medium">Airline</Label>
                            <Input
                                value={targetAirline || ''}
                                disabled
                                className="mt-1"
                                placeholder="Select airline from Dashboard"
                            />
                        </div>
                        <div className="flex-1">
                            <Label className="text-sm font-medium">Start Date</Label>
                            <Input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="mt-1"
                            />
                        </div>
                        <div className="flex-1">
                            <Label className="text-sm font-medium">End Date</Label>
                            <Input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="mt-1"
                            />
                        </div>
                        <div className="flex-1">
                            <Label className="text-sm font-medium">Sort By</Label>
                            <Select value={sortBy} onValueChange={setSortBy}>
                                <SelectTrigger className="mt-1">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="coef">Coefficient</SelectItem>
                                    <SelectItem value="p_value">P-Value</SelectItem>
                                    <SelectItem value="topic_id">Topic ID</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    
                    {/* 模型统计 */}
                    {driversData && driversData.status !== 'needs_mining' && (() => {
                        const actualData = driversData.status === 'success' ? driversData.data : driversData;
                        return actualData ? (
                            <div className="flex gap-4 text-sm text-gray-600">
                                <span>R²: {actualData.model_r_squared?.toFixed(4) || 'N/A'}</span>
                                <span>Sample Size: {actualData.sample_size?.toLocaleString() || 'N/A'}</span>
                            </div>
                        ) : null;
                    })()}
                    
                    {/* Topic Mining 状态 */}
                    {miningStatus === 'mining' && (
                        <div className="flex flex-col items-center justify-center py-8 space-y-4">
                            <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                            <div className="text-lg font-semibold text-[#5D5FEF]">
                                {miningMessage || 'Executing topic mining, please wait...'}
                            </div>
                            <div className="text-sm text-gray-500">
                                This may take a few minutes depending on the amount of data.
                            </div>
                        </div>
                    )}
                    
                    {miningStatus === 'success' && (
                        <div className="flex flex-col items-center justify-center py-8 space-y-4">
                            <div className="text-lg font-semibold text-green-600">
                                ✅ {miningMessage || 'Topic mining completed!'}
                            </div>
                        </div>
                    )}
                    
                    {miningStatus === 'error' && (
                        <div className="flex flex-col items-center justify-center py-8 space-y-4">
                            <div className="text-lg font-semibold text-red-600">
                                ❌ {miningMessage || 'Topic mining failed'}
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                    setMiningStatus(null);
                                    setMiningMessage('');
                                    runTopicMining();
                                }}
                            >
                                Retry
                            </Button>
                        </div>
                    )}
                    
                    {/* 加载状态 */}
                    {driversLoading && !miningStatus ? (
                        <div className="flex items-center justify-center py-8">
                            <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                        </div>
                    ) : !targetAirline ? (
                        <div className="text-center py-8 text-gray-500">
                            Please select an airline from Dashboard
                        </div>
                    ) : !driversData || driversData.status === 'needs_mining' || (() => {
                        const actualData = driversData?.status === 'success' ? driversData.data : driversData;
                        return !actualData?.topics || actualData.topics.length === 0;
                    })() ? (
                        <div className="text-center py-8 text-gray-500">
                            {driversData?.status === 'needs_mining' 
                                ? 'No topic data available. Topic mining will start automatically...'
                                : 'No topic driver data available. Click "Refresh" to compute.'}
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* 正向 Topics */}
                            <div>
                                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                                    <TrendingUp className="w-5 h-5 text-green-600" />
                                    Topics That Increase Ratings (Positive Coefficients)
                                </h3>
                                <div className="space-y-2">
                                    {positiveTopics.map((topic) => (
                                        <div
                                            key={topic.topic_label || `topic-${topic.topic_id}`}
                                            className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                                                selectedTopic === topic.topic_id
                                                    ? 'border-green-500 bg-green-50'
                                                    : 'border-gray-200 hover:border-green-300'
                                            }`}
                                            onClick={() => handleTopicClick(topic.topic_id)}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <span className="font-semibold">{topic.topic_label || `Topic ${topic.topic_id}`}</span>
                                                        <span className="text-xs text-gray-500">(ID: {topic.topic_id})</span>
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleAddTopicToSimulator(topic);
                                                            }}
                                                            className="ml-2 h-6 text-xs"
                                                        >
                                                            Add to Simulator
                                                        </Button>
                                                    </div>
                                                    {topic.top_words && topic.top_words.length > 0 && (
                                                        <div className="text-sm text-gray-600 mb-2">
                                                            Top Words: {topic.top_words.slice(0, 5).join(', ')}
                                                        </div>
                                                    )}
                                                    <div className="flex gap-4 text-sm">
                                                        <span>Coef: <strong className="text-green-600">{topic.coef.toFixed(4)}</strong></span>
                                                        <span>P-value: {topic.p_value.toFixed(4)}</span>
                                                        <span>CI: [{topic.ci_low.toFixed(4)}, {topic.ci_high.toFixed(4)}]</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    {positiveTopics.length === 0 && (
                                        <div className="text-center py-4 text-gray-500">No positive topics found</div>
                                    )}
                                </div>
                            </div>
                            
                            {/* 负向 Topics */}
                            <div>
                                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                                    <TrendingDown className="w-5 h-5 text-red-600" />
                                    Topics That Decrease Ratings (Negative Coefficients)
                                </h3>
                                <div className="space-y-2">
                                    {negativeTopics.map((topic) => (
                                        <div
                                            key={topic.topic_label || `topic-${topic.topic_id}`}
                                            className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                                                selectedTopic === topic.topic_id
                                                    ? 'border-red-500 bg-red-50'
                                                    : 'border-gray-200 hover:border-red-300'
                                            }`}
                                            onClick={() => handleTopicClick(topic.topic_id)}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <span className="font-semibold">{topic.topic_label || `Topic ${topic.topic_id}`}</span>
                                                        <span className="text-xs text-gray-500">(ID: {topic.topic_id})</span>
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleAddTopicToSimulator(topic);
                                                            }}
                                                            className="ml-2 h-6 text-xs"
                                                        >
                                                            Add to Simulator
                                                        </Button>
                                                    </div>
                                                    {topic.top_words && topic.top_words.length > 0 && (
                                                        <div className="text-sm text-gray-600 mb-2">
                                                            Top Words: {topic.top_words.slice(0, 5).join(', ')}
                                                        </div>
                                                    )}
                                                    <div className="flex gap-4 text-sm">
                                                        <span>Coef: <strong className="text-red-600">{topic.coef.toFixed(4)}</strong></span>
                                                        <span>P-value: {topic.p_value.toFixed(4)}</span>
                                                        <span>CI: [{topic.ci_low.toFixed(4)}, {topic.ci_high.toFixed(4)}]</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    {negativeTopics.length === 0 && (
                                        <div className="text-center py-4 text-gray-500">No negative topics found</div>
                                    )}
                                    {/* 移除可能显示 0 的地方 */}
                                </div>
                            </div>
                            
                            {/* 代表性评论 */}
                            {selectedTopic && (
                                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                                    <h4 className="font-semibold mb-3">Representative Reviews for Selected Topic</h4>
                                    {loadingReviews ? (
                                        <Spinner className="w-6 h-6" />
                                    ) : representativeReviews.length > 0 ? (
                                        <div className="space-y-2">
                                            {representativeReviews.map((review) => (
                                                <div key={review.reviewId} className="p-3 bg-white rounded border">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className="font-medium">Rating: {review.score}/10</span>
                                                        {review.sentiment_label && (
                                                            <span className={`px-2 py-0.5 rounded text-xs ${
                                                                review.sentiment_label === 'Positive' ? 'bg-green-100 text-green-700' :
                                                                review.sentiment_label === 'Negative' ? 'bg-red-100 text-red-700' :
                                                                'bg-gray-100 text-gray-700'
                                                            }`}>
                                                                {review.sentiment_label}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="text-sm text-gray-700">{review.content}</div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="text-gray-500">No reviews found</div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>
            
            {/* 模拟器面板 */}
            {showSimulator && (
                <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80]">
                    <CardHeader>
                        <CardTitle className="text-xl font-semibold">Rating Improvement Simulator</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* 模拟器输入（固定为 Drivers 面板的值） */}
                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <Label className="text-sm font-medium">Airline</Label>
                                <Input
                                    value={simulatorAirline}
                                    disabled
                                    className="mt-1 bg-gray-50"
                                    placeholder="Same as Drivers panel"
                                />
                            </div>
                            <div>
                                <Label className="text-sm font-medium">Start Date</Label>
                                <Input
                                    type="date"
                                    value={simulatorStartDate}
                                    disabled
                                    className="mt-1 bg-gray-50"
                                />
                            </div>
                            <div>
                                <Label className="text-sm font-medium">End Date</Label>
                                <Input
                                    type="date"
                                    value={simulatorEndDate}
                                    disabled
                                    className="mt-1 bg-gray-50"
                                />
                            </div>
                        </div>
                        <p className="text-xs text-gray-500">
                            Simulator uses the same filters as the Drivers panel above
                        </p>
                        
                        {/* 选择的 Topics */}
                        {selectedTopics.length > 0 && (
                            <div className="space-y-3">
                                <Label className="text-sm font-medium">Selected Topics (Max 3)</Label>
                                {selectedTopics.map((topic) => {
                                    const isNegative = topic.coef < 0;
                                    const changeLabel = topic.share_change_pct > 0 
                                        ? `Increase: +${topic.share_change_pct}%` 
                                        : `Decrease: ${topic.share_change_pct}%`;
                                    const changeColor = topic.share_change_pct > 0 ? 'text-green-600' : 'text-red-600';
                                    
                                    return (
                                        <div key={`${topic.topic_id}-${topic.topic_label}`} className="p-3 bg-gray-50 rounded-lg">
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium">{topic.topic_label || `Topic ${topic.topic_id}`}</span>
                                                    <span className={`text-xs px-2 py-0.5 rounded ${
                                                        isNegative ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                                                    }`}>
                                                        {isNegative ? 'Negative' : 'Positive'} Topic
                                                    </span>
                                                </div>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleRemoveTopic(topic.topic_label)}
                                                    className="h-6 text-xs"
                                                >
                                                    Remove
                                                </Button>
                                            </div>
                                            <div className="space-y-2">
                                                <div className="flex items-center gap-4">
                                                    <Label className={`text-xs font-medium ${changeColor}`}>
                                                        {changeLabel}
                                                    </Label>
                                                    <input
                                                        type="range"
                                                        min="-50"
                                                        max="50"
                                                        step="1"
                                                        value={topic.share_change_pct}
                                                        onChange={(e) => handleUpdateTopicChange(topic.topic_label, parseFloat(e.target.value))}
                                                        className="flex-1"
                                                    />
                                                </div>
                                                <p className="text-xs text-gray-500">
                                                    {isNegative 
                                                        ? 'Decrease this negative topic to improve ratings' 
                                                        : 'Increase this positive topic to improve ratings'}
                                                </p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                        
                        {/* 运行模拟按钮 */}
                        <Button
                            onClick={handleSimulate}
                            disabled={simulating || !simulatorAirline || selectedTopics.length === 0}
                            className="w-full"
                        >
                            {simulating ? 'Simulating...' : 'Run Simulation'}
                        </Button>
                        
                        {/* 模拟结果 */}
                        {simulationResult && (
                            <div className="p-4 bg-blue-50 rounded-lg space-y-3">
                                <h4 className="font-semibold">Simulation Results</h4>
                                
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-sm text-gray-600">Current Avg Rating</div>
                                        <div className="text-2xl font-bold">{simulationResult.current_avg_rating?.toFixed(2)}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-gray-600">Predicted Avg Rating</div>
                                        <div className="text-2xl font-bold text-green-600">
                                            {simulationResult.predicted_avg_rating?.toFixed(2)}
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="p-3 bg-white rounded border">
                                    <div className="flex items-center gap-2 mb-2">
                                        <ArrowUp className="w-5 h-5 text-green-600" />
                                        <span className="font-semibold">Rating Improvement</span>
                                    </div>
                                    <div className="text-2xl font-bold text-green-600">
                                        +{simulationResult.delta_rating?.toFixed(3)}
                                    </div>
                                    <div className="text-sm text-gray-600 mt-1">
                                        Uncertainty Interval: [{simulationResult.delta_rating_low?.toFixed(3)}, {simulationResult.delta_rating_high?.toFixed(3)}]
                                    </div>
                                </div>
                                
                                {/* Topic Impacts */}
                                {simulationResult.topic_impacts && simulationResult.topic_impacts.length > 0 && (
                                    <div>
                                        <h5 className="font-semibold mb-2">Topic Impacts</h5>
                                        <div className="space-y-2">
                                            {simulationResult.topic_impacts.map((impact) => (
                                                <div key={impact.topic_id} className="p-2 bg-white rounded border text-sm">
                                                    <div className="flex items-center justify-between">
                                                        <span>{impact.topic_label}</span>
                                                        <span className="text-green-600 font-medium">
                                                            +{impact.delta_rating?.toFixed(3)}
                                                        </span>
                                                    </div>
                                                    <div className="text-xs text-gray-500">
                                                        Change: {impact.share_change_pct !== undefined 
                                                            ? (impact.share_change_pct > 0 ? '+' : '') + impact.share_change_pct.toFixed(1) + '%'
                                                            : (impact.share_reduction_pct !== undefined ? '-' + impact.share_reduction_pct.toFixed(1) + '%' : 'N/A')} | 
                                                        ROI: {impact.roi?.toFixed(3)} per 1% change
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                
                                {/* Priority Rankings */}
                                {simulationResult.priority_rankings && simulationResult.priority_rankings.length > 0 && (
                                    <div>
                                        <h5 className="font-semibold mb-2 flex items-center gap-2">
                                            <AlertCircle className="w-4 h-4" />
                                            Priority Rankings (by ROI)
                                        </h5>
                                        <div className="space-y-1">
                                            {simulationResult.priority_rankings.map((ranking, idx) => (
                                                <div key={ranking.topic_id} className="flex items-center justify-between p-2 bg-white rounded border text-sm">
                                                    <span>
                                                        {idx + 1}. {ranking.topic_label}
                                                    </span>
                                                    <span className="font-medium">
                                                        ROI: {ranking.roi?.toFixed(3)}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                
                                <div className="text-xs text-gray-500 mt-2">
                                    Model R²: {simulationResult.model_r_squared?.toFixed(4)} | 
                                    Sample Size: {simulationResult.sample_size?.toLocaleString()}
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}
            </div>
            
            {/* 右侧：AirSight RAG 对话框 */}
            <div className="w-96 flex-shrink-0">
                <AirSightDialog
                    airlineName={targetAirline}
                    startDate={startDate}
                    endDate={endDate}
                    destination={null}
                    sentiment={null}
                />
            </div>
        </div>
    );
};

export default Analytics;
