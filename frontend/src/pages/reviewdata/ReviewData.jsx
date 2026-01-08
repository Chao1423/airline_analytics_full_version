import React, { useState, useMemo, useEffect, useRef } from "react";
import { useReactTable, getCoreRowModel, getPaginationRowModel, flexRender, getSortedRowModel } from "@tanstack/react-table";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuCheckboxItem } from "@/components/ui/dropdown-menu";
import { ChevronDown, X } from "lucide-react";
import { FaSortUp, FaSortDown } from "react-icons/fa6";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";

// 关键词高亮组件
const HighlightText = ({ text, keywords = [], className = "" }) => {
    if (!text || !keywords || keywords.length === 0) {
        return <span className={className}>{text}</span>;
    }
    
    // 创建正则表达式匹配所有关键词（不区分大小写）
    const pattern = new RegExp(`(${keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
    const parts = text.split(pattern);
    
    return (
        <span className={className}>
            {parts.map((part, index) => {
                const isKeyword = keywords.some(k => part.toLowerCase() === k.toLowerCase());
                return isKeyword ? (
                    <mark key={index} className="bg-yellow-200 px-1 rounded">
                        {part}
                    </mark>
                ) : (
                    <span key={index}>{part}</span>
                );
            })}
        </span>
    );
};

const ReviewData = () => {
    const targetAirline = useContext((state) => state.targetAirline);
    const tableRef = useRef(null);
    
    // 筛选状态
    const [filters, setFilters] = useState({
        start_date: '',
        end_date: '',
        min_rating: '',
        max_rating: '',
        sentiment: '',
        topic_id: null,
        aspect: '',
        destination: ''
    });
    
    // 分页状态
    const [page, setPage] = useState(1);
    const pageSize = 20;
    
    // 点击的 topic（用于自动筛选和滚动）
    const [clickedTopic, setClickedTopic] = useState(null);
    
    // 构建 API URL
    const url = useMemo(() => {
        if (!targetAirline) return null;
        
        const params = new URLSearchParams({
            airline_name: targetAirline,
            page: page.toString(),
            page_size: pageSize.toString()
        });
        
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        if (filters.min_rating) params.append('min_rating', filters.min_rating);
        if (filters.max_rating) params.append('max_rating', filters.max_rating);
        if (filters.sentiment) params.append('sentiment', filters.sentiment);
        if (filters.topic_id) params.append('topic_id', filters.topic_id.toString());
        if (filters.aspect) params.append('aspect', filters.aspect);
        if (filters.destination) params.append('destination', filters.destination);
        
        return `/api/reviews/search?${params.toString()}`;
    }, [targetAirline, filters, page]);
    
    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });
    
    // 处理点击 topic
    useEffect(() => {
        if (clickedTopic !== null) {
            setFilters(prev => ({ ...prev, topic_id: clickedTopic }));
            setPage(1);
            setClickedTopic(null);
            
            // 滚动到表格顶部
            setTimeout(() => {
                if (tableRef.current) {
                    tableRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        }
    }, [clickedTopic]);
    
    // 重置筛选
    const resetFilters = () => {
        setFilters({
            start_date: '',
            end_date: '',
            min_rating: '',
            max_rating: '',
            sentiment: '',
            topic_id: null,
            aspect: '',
            destination: ''
        });
        setPage(1);
    };
    
    // 获取高亮关键词
    const getHighlightKeywords = (review) => {
        const keywords = [];
        
        // 添加 topic 关键词
        if (review.topic_words && Array.isArray(review.topic_words)) {
            keywords.push(...review.topic_words.slice(0, 5));
        }
        
        // 添加 aspect 关键词
        if (review.matched_aspects && Array.isArray(review.matched_aspects)) {
            const aspectKeywords = {
                'Seat Comfort': ['seat', 'comfortable', 'legroom', 'space'],
                'Cabin Staff & Service': ['staff', 'crew', 'service', 'friendly'],
                'Food & Beverages': ['food', 'meal', 'dinner', 'taste'],
                'Inflight Entertainment': ['entertainment', 'movie', 'music'],
                'Ground Service': ['ground', 'check-in', 'boarding'],
                'Wifi Connectivity': ['wifi', 'internet', 'connection'],
                'Value for Money': ['price', 'cost', 'value', 'money']
            };
            review.matched_aspects.forEach(aspect => {
                if (aspectKeywords[aspect]) {
                    keywords.push(...aspectKeywords[aspect]);
                }
            });
        }
        
        return [...new Set(keywords)]; // 去重
    };
    
    const columns = [
        {
            id: "index",
            header: "#",
            cell: ({ row }) => (page - 1) * pageSize + row.index + 1,
            enableSorting: false,
            size: 50,
        },
        {
            accessorKey: "title",
            header: "Title",
            cell: ({ row }) => {
                const review = row.original;
                const keywords = getHighlightKeywords(review);
                return (
                    <HighlightText 
                        text={review.title || ''} 
                        keywords={keywords}
                        className="font-medium"
                    />
                );
            },
            size: 200,
        },
        {
            accessorKey: "score",
            header: ({ column }) => (
                <Button
                    variant="ghost"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                    className="ml-2 hover:bg-transparent font-bold flex items-center"
                >
                    Score
                    <div className="flex flex-col">
                        <FaSortUp 
                            style={{ width: '20px', height: '20px' }}
                            className={`-mb-2.5 ${column.getIsSorted() === "asc" ? "text-black" : "text-gray-400"}`} 
                        />
                        <FaSortDown
                            style={{ width: '20px', height: '20px' }} 
                            className={`-mt-2.5 ${column.getIsSorted() === "desc" ? "text-black" : "text-gray-400"}`} 
                        />
                    </div>
                </Button>
            ),
            cell: ({ row }) => (
                <div className="flex items-center justify-center">
                    <span className="font-semibold text-[#5D5FEF]">{row.getValue("score") || 'N/A'}</span>
                    {row.getValue("score") && <span className="text-gray-500 ml-1">/ 10</span>}
                </div>
            ),
            enableSorting: true,
            size: 100,
        },
        {
            accessorKey: "content",
            header: "Content",
            cell: ({ row }) => {
                const review = row.original;
                const keywords = getHighlightKeywords(review);
                const content = review.content || '';
                return (
                    <div className="max-w-xs truncate" title={content}>
                        <HighlightText 
                            text={content.length > 100 ? content.substring(0, 100) + '...' : content}
                            keywords={keywords}
                            className="text-sm"
                        />
                    </div>
                );
            },
            size: 250,
        },
        {
            accessorKey: "sentiment_label",
            header: "Sentiment",
            cell: ({ row }) => {
                const label = row.getValue("sentiment_label");
                const colorMap = {
                    'Positive': 'bg-green-100 text-green-700',
                    'Negative': 'bg-red-100 text-red-700',
                    'Neutral': 'bg-gray-100 text-gray-700'
                };
                return (
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colorMap[label] || 'bg-gray-100 text-gray-700'}`}>
                        {label || 'N/A'}
                    </span>
                );
            },
            size: 100,
        },
        {
            accessorKey: "topic_label",
            header: "Topic",
            cell: ({ row }) => {
                const topicLabel = row.getValue("topic_label");
                const topicId = row.original.topic_id;
                if (!topicLabel) return <span className="text-gray-400">-</span>;
                return (
                    <button
                        onClick={() => setClickedTopic(topicId)}
                        className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors cursor-pointer"
                        title="Click to filter by this topic"
                    >
                        {topicLabel}
                    </button>
                );
            },
            size: 150,
        },
        {
            accessorKey: "matched_aspects",
            header: "Aspects",
            cell: ({ row }) => {
                const aspects = row.getValue("matched_aspects") || [];
                if (aspects.length === 0) return <span className="text-gray-400">-</span>;
                return (
                    <div className="flex flex-wrap gap-1">
                        {aspects.slice(0, 3).map((aspect, idx) => (
                            <span
                                key={idx}
                                className="px-2 py-0.5 rounded text-xs bg-purple-100 text-purple-700"
                            >
                                {aspect}
                            </span>
                        ))}
                        {aspects.length > 3 && (
                            <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
                                +{aspects.length - 3}
                            </span>
                        )}
                    </div>
                );
            },
            size: 200,
        },
        {
            accessorKey: "reviewDate",
            header: "Date",
            cell: ({ row }) => <span className="text-sm">{row.getValue("reviewDate") || 'N/A'}</span>,
            size: 100,
        },
    ];
    
    const reviewData = useMemo(() => {
        if (!data) return [];
        // useQuery 返回的 data 结构：{ status: "success", data: {...} }
        // 或者直接是 { reviews: [...], pagination: {...}, summary: {...} }
        const actualData = (data.status === 'success' && data.data) ? data.data : data;
        if (!actualData || !actualData.reviews) return [];
        return actualData.reviews;
    }, [data]);
    
    const summary = useMemo(() => {
        if (!data) return null;
        const actualData = (data.status === 'success' && data.data) ? data.data : data;
        if (!actualData || !actualData.summary) return null;
        return actualData.summary;
    }, [data]);
    
    const pagination = useMemo(() => {
        if (!data) return { page: 1, page_size: 20, total_count: 0, total_pages: 0 };
        const actualData = (data.status === 'success' && data.data) ? data.data : data;
        if (!actualData || !actualData.pagination) return { page: 1, page_size: 20, total_count: 0, total_pages: 0 };
        return actualData.pagination;
    }, [data]);
    
    const table = useReactTable({
        data: reviewData,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        getSortedRowModel: getSortedRowModel(),
        manualPagination: true,
        pageCount: pagination.total_pages || 0,
    });
    
    return (
        <div className="flex gap-4 p-4 h-full">
            {/* 左侧筛选栏 */}
            <Card className="w-80 h-fit bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80]">
                <CardHeader>
                    <CardTitle className="text-lg font-semibold flex items-center justify-between">
                        <span>Filters</span>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={resetFilters}
                            className="h-8 text-xs"
                        >
                            <X className="h-4 w-4 mr-1" />
                            Reset
                        </Button>
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Time Range */}
                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Time Range</Label>
                        <div className="flex gap-2">
                            <Input
                                type="date"
                                value={filters.start_date}
                                onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value }))}
                                className="h-9 text-sm"
                            />
                            <Input
                                type="date"
                                value={filters.end_date}
                                onChange={(e) => setFilters(prev => ({ ...prev, end_date: e.target.value }))}
                                className="h-9 text-sm"
                            />
                        </div>
                    </div>
                    
                    {/* Rating */}
                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Rating</Label>
                        <div className="flex gap-2">
                            <Input
                                type="number"
                                placeholder="Min"
                                min="0"
                                max="10"
                                value={filters.min_rating}
                                onChange={(e) => setFilters(prev => ({ ...prev, min_rating: e.target.value }))}
                                className="h-9 text-sm"
                            />
                            <Input
                                type="number"
                                placeholder="Max"
                                min="0"
                                max="10"
                                value={filters.max_rating}
                                onChange={(e) => setFilters(prev => ({ ...prev, max_rating: e.target.value }))}
                                className="h-9 text-sm"
                            />
                        </div>
                    </div>
                    
                    {/* Sentiment */}
                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Sentiment</Label>
                        <Select
                            value={filters.sentiment}
                            onValueChange={(value) => setFilters(prev => ({ ...prev, sentiment: value }))}
                        >
                            <SelectTrigger className="h-9 text-sm">
                                <SelectValue placeholder="All" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="">All</SelectItem>
                                <SelectItem value="pos">Positive</SelectItem>
                                <SelectItem value="neg">Negative</SelectItem>
                                <SelectItem value="neutral">Neutral</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    
                    {/* Topic */}
                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Topic</Label>
                        <Select
                            value={filters.topic_id ? filters.topic_id.toString() : ''}
                            onValueChange={(value) => setFilters(prev => ({ ...prev, topic_id: value ? parseInt(value) : null }))}
                        >
                            <SelectTrigger className="h-9 text-sm">
                                <SelectValue placeholder="All Topics" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="">All Topics</SelectItem>
                                {summary?.top_topics?.map(topic => (
                                    <SelectItem key={topic.topic_id} value={topic.topic_id.toString()}>
                                        {topic.label} ({topic.count})
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    
                    {/* Aspect */}
                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Aspect</Label>
                        <Select
                            value={filters.aspect}
                            onValueChange={(value) => setFilters(prev => ({ ...prev, aspect: value }))}
                        >
                            <SelectTrigger className="h-9 text-sm">
                                <SelectValue placeholder="All Aspects" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="">All Aspects</SelectItem>
                                <SelectItem value="Seat Comfort">Seat Comfort</SelectItem>
                                <SelectItem value="Cabin Staff & Service">Cabin Staff & Service</SelectItem>
                                <SelectItem value="Food & Beverages">Food & Beverages</SelectItem>
                                <SelectItem value="Inflight Entertainment">Inflight Entertainment</SelectItem>
                                <SelectItem value="Ground Service">Ground Service</SelectItem>
                                <SelectItem value="Wifi Connectivity">Wifi Connectivity</SelectItem>
                                <SelectItem value="Value for Money">Value for Money</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    
                    {/* Destination */}
                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Destination</Label>
                        <Input
                            placeholder="Enter destination..."
                            value={filters.destination}
                            onChange={(e) => setFilters(prev => ({ ...prev, destination: e.target.value }))}
                            className="h-9 text-sm"
                        />
                    </div>
                    
                    {/* 聚合摘要 */}
                    {summary && (
                        <div className="pt-4 border-t space-y-2">
                            <Label className="text-sm font-semibold">Summary</Label>
                            <div className="text-xs space-y-1">
                                <div>Total: {summary.count || 0} reviews</div>
                                {summary.avg_rating && (
                                    <div>Avg Rating: {summary.avg_rating.toFixed(2)}</div>
                                )}
                            </div>
                            
                            {summary.top_topics && summary.top_topics.length > 0 && (
                                <div className="mt-3">
                                    <Label className="text-xs font-medium text-gray-600">Top Topics</Label>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                        {summary.top_topics.map(topic => (
                                            <button
                                                key={topic.topic_id}
                                                onClick={() => setClickedTopic(topic.topic_id)}
                                                className="px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors"
                                            >
                                                {topic.label} ({topic.count})
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                            
                            {summary.top_aspects && summary.top_aspects.length > 0 && (
                                <div className="mt-3">
                                    <Label className="text-xs font-medium text-gray-600">Top Aspects</Label>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                        {summary.top_aspects.map(aspect => (
                                            <span
                                                key={aspect.aspect}
                                                className="px-2 py-0.5 rounded text-xs bg-purple-100 text-purple-700"
                                            >
                                                {aspect.aspect} ({aspect.count})
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>
            
            {/* 右侧表格 */}
            <Card className="flex-1 bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] flex flex-col gap-2 overflow-hidden">
                {!targetAirline ? (
                    <div className="flex-1 flex items-center justify-center h-full">
                        <div className="text-xl font-semibold text-center">
                            ✈️ Please search for an airline to view reviews
                        </div>
                    </div>
                ) : loading ? (
                    <div className="flex-1 flex items-center justify-center">
                        <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                    </div>
                ) : (
                    <>
                        <div className="p-4 border-b">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-semibold">Review Data</h2>
                                <div className="text-sm text-gray-500">
                                    Showing {pagination.total_count} reviews
                                </div>
                            </div>
                        </div>
                        
                        <div className="flex-1 overflow-auto" ref={tableRef}>
                            <Table>
                                <TableHeader>
                                    {table.getHeaderGroups().map((headerGroup) => (
                                        <TableRow key={headerGroup.id}>
                                            {headerGroup.headers.map((header) => (
                                                <TableHead 
                                                    key={header.id} 
                                                    className="font-bold text-center"
                                                    style={{ width: header.getSize(), minWidth: header.getSize() }}
                                                >
                                                    {flexRender(header.column.columnDef.header, header.getContext())}
                                                </TableHead>
                                            ))}
                                        </TableRow>
                                    ))}
                                </TableHeader>
                                <TableBody>
                                    {table.getRowModel().rows.length ? (
                                        table.getRowModel().rows.map((row) => (
                                            <TableRow key={row.id}>
                                                {row.getVisibleCells().map((cell) => (
                                                    <TableCell 
                                                        key={cell.id}
                                                        className={`${cell.column.id === 'content' ? 'text-left' : 'text-center'}`}
                                                        style={{ 
                                                            maxWidth: cell.column.id === 'content' ? '250px' : 'none',
                                                            overflow: cell.column.id === 'content' ? 'hidden' : 'visible',
                                                            textOverflow: cell.column.id === 'content' ? 'ellipsis' : 'clip'
                                                        }}
                                                    >
                                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                                    </TableCell>
                                                ))}
                                            </TableRow>
                                        ))
                                    ) : (
                                        <TableRow>
                                            <TableCell colSpan={columns.length} className="text-center py-8">
                                                <span className="text-xl font-semibold">🔍 No reviews found</span>
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                        
                        <div className="p-4 border-t flex items-center justify-between">
                            <div className="text-sm text-gray-500">
                                Page {pagination.page} of {pagination.total_pages || 1}
                            </div>
                            <div className="flex items-center gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={pagination.page <= 1}
                                >
                                    Previous
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setPage(p => Math.min(pagination.total_pages || 1, p + 1))}
                                    disabled={pagination.page >= (pagination.total_pages || 1)}
                                >
                                    Next
                                </Button>
                            </div>
                        </div>
                    </>
                )}
            </Card>
        </div>
    );
};

export default ReviewData;
