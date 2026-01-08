import { Card, CardContent } from "@/components/ui/card";
import React, { useEffect, useRef, useMemo, useState } from "react";
import { init } from "echarts";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";

export default function TopTopicsSection() {
    const chartRef = useRef(null);
    const targetAirline = useContext((state) => state.targetAirline);
    const [sentiment, setSentiment] = useState('pos'); // 'pos' or 'neg'

    // 同时预加载 pos 和 neg 数据，避免切换时重新加载
    const posUrl = useMemo(() => {
        if (!targetAirline) return null;
        return `/api/airlines/${encodeURIComponent(targetAirline)}/top-topics?sentiment=pos&n=10`;
    }, [targetAirline]);

    const negUrl = useMemo(() => {
        if (!targetAirline) return null;
        return `/api/airlines/${encodeURIComponent(targetAirline)}/top-topics?sentiment=neg&n=10`;
    }, [targetAirline]);

    // 预加载两种 sentiment 的数据
    const { data: posData } = useQuery(posUrl, {
        cacheTime: 10 * 60 * 1000,
        staleTime: 5 * 60 * 1000,
        refetchOnMount: false,
    });

    const { data: negData, loading: negLoading } = useQuery(negUrl, {
        cacheTime: 10 * 60 * 1000,
        staleTime: 5 * 60 * 1000,
        refetchOnMount: false,
    });

    // 根据当前 sentiment 选择数据
    const data = sentiment === 'pos' ? posData : negData;
    const loading = sentiment === 'pos' ? false : negLoading; // pos 数据已经在初始加载时获取

    useEffect(() => {
        if (!chartRef.current || !data || !Array.isArray(data) || data.length === 0) return;

        const chart = init(chartRef.current);

        // 准备数据：按 review_count 排序
        // 对于 review_count = 0 的主题，用很小的值（0.01）代替，以便在饼图中显示但几乎不可见
        const sortedData = [...data].sort((a, b) => b.review_count - a.review_count);
        
        const displayData = sortedData.map(t => ({
            ...t,
            review_count: t.review_count || 0.01 // 用 0.01 代替 0，以便在饼图中显示
        }));

        const pieData = displayData.map((topic, index) => ({
            value: topic.review_count,
            name: topic.human_label || `Topic ${topic.topic_id}`,
            itemStyle: {
                color: sentiment === 'pos' 
                    ? ['#10b981', '#22c55e', '#4ade80', '#86efac', '#bbf7d0'][index % 5] || '#10b981'
                    : ['#ef4444', '#f87171', '#fca5a5', '#fecaca', '#fee2e2'][index % 5] || '#ef4444'
            }
        }));

        const option = {
            tooltip: {
                trigger: 'item',
                formatter: (params) => {
                    const topic = displayData[params.dataIndex];
                    const actualCount = topic.review_count === 0.01 ? 0 : topic.review_count;
                    let result = `<strong>${params.name}</strong><br/>`;
                    result += `Review Count: ${actualCount}${actualCount === 0 ? ' (No reviews)' : ''}<br/>`;
                    if (actualCount > 0) {
                        result += `Avg Score: ${(topic.avg_score * 100).toFixed(2)}%<br/>`;
                        result += `Top Words: ${topic.top_words?.slice(0, 5).join(', ') || 'N/A'}<br/>`;
                        result += `Percentage: ${params.percent}%`;
                    } else {
                        result += `This topic has no reviews for this airline`;
                    }
                    return result;
                }
            },
            legend: {
                orient: 'vertical',
                left: 'left',
                top: 'middle',
                textStyle: {
                    fontSize: 11
                },
                formatter: (name) => {
                    // 截断过长的标签
                    return name.length > 20 ? name.substring(0, 20) + '...' : name;
                }
            },
            series: [
                {
                    name: 'Review Count',
                    type: 'pie',
                    radius: ['40%', '70%'], // 环形图
                    center: ['60%', '50%'],
                    avoidLabelOverlap: true,
                    itemStyle: {
                        borderRadius: 8,
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: true,
                        formatter: (params) => {
                            // 对于 review_count = 0 的主题，不显示百分比
                            const topic = displayData[params.dataIndex];
                            if (topic.review_count === 0.01) {
                                return '';
                            }
                            return `${params.percent}%`;
                        },
                        fontSize: 11
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 14,
                            fontWeight: 'bold'
                        },
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    },
                    labelLine: {
                        show: true
                    },
                    data: pieData
                }
            ]
        };

        chart.setOption(option);

        const resizeObserver = new ResizeObserver(() => {
            chart.resize();
        });

        if (chartRef.current) {
            resizeObserver.observe(chartRef.current);
        }

        return () => {
            resizeObserver.disconnect();
            chart.dispose();
        };
    }, [data, sentiment]);

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] min-h-[300px]">
            {!targetAirline ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        ✈️ Please search for an airline to view top topics
                    </div>
                </div>
            ) : loading ? (
                <div className="flex items-center justify-center h-full">
                    <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                </div>
            ) : !data || !Array.isArray(data) || data.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                        <div className="text-xl font-semibold mb-2">
                            😢 No topic data available
                        </div>
                        <div className="text-sm text-gray-500">
                            Run topic mining pipeline to generate topics
                        </div>
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 pt-4 text-xl font-semibold flex items-center justify-between pr-6">
                        <span>Top Topics</span>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setSentiment('pos')}
                                className={`px-4 py-1 rounded-lg text-sm font-medium transition-colors ${
                                    sentiment === 'pos'
                                        ? 'bg-green-100 text-green-700 border-2 border-green-500'
                                        : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                                }`}
                            >
                                Positive
                            </button>
                            <button
                                onClick={() => setSentiment('neg')}
                                className={`px-4 py-1 rounded-lg text-sm font-medium transition-colors ${
                                    sentiment === 'neg'
                                        ? 'bg-red-100 text-red-700 border-2 border-red-500'
                                        : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                                }`}
                            >
                                Negative
                            </button>
                        </div>
                    </div>
                    <CardContent className="flex flex-1 min-h-[250px]">
                        <div ref={chartRef} className="w-full h-full" />
                    </CardContent>
                    <div className="pl-6 pb-4 text-xs text-gray-500">
                        Showing {data.length} {sentiment === 'pos' ? 'positive' : 'negative'} topics ({data.filter(t => t.review_count > 0).length} with reviews, {data.filter(t => t.review_count === 0).length} without)
                    </div>
                </>
            )}
        </Card>
    );
}

