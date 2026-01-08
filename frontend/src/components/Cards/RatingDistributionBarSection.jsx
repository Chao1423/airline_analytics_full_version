import { Card, CardContent } from "@/components/ui/card";
import React, { useEffect, useRef, useMemo } from "react";
import { init } from "echarts";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";

export default function RatingDistributionBarSection() {
    const chartRef = useRef(null);
    const targetAirline = useContext((state) => state.targetAirline);
    
    const url = useMemo(() => {
        if (!targetAirline) return null;
        return `/airlines/${encodeURIComponent(targetAirline)}/rating-distribution`;
    }, [targetAirline]);
    
    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    useEffect(() => {
        if (!chartRef.current || !data || !Array.isArray(data) || data.length === 0) return;

        const chart = init(chartRef.current);

        // Transform data: [{rating: 1, count: 10}, ...] -> [10, 20, ...]
        const ratingData = data.map(item => item.count);
        const totalCount = ratingData.reduce((sum, count) => sum + count, 0);

        const option = {
            grid: {
                top: '10%',
                left: '10%',
                right: '10%',
                bottom: '10%',
                containLabel: true
            },
            tooltip: {
                trigger: "axis",
                axisPointer: {
                    type: 'shadow'
                },
                formatter: (params) => {
                    const param = params[0];
                    const rating = param.name;
                    const count = param.value;
                    const percentage = totalCount > 0 ? ((count / totalCount) * 100).toFixed(1) : 0;
                    return `Rating ${rating}: ${count} reviews (${percentage}%)`;
                }
            },
            xAxis: {
                type: "category",
                data: data.map(item => `Rating ${item.rating}`),
                axisLine: {
                    lineStyle: {
                        color: '#e0e0e0'
                    }
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#666',
                    fontSize: 12
                }
            },
            yAxis: {
                type: "value",
                name: 'Number of Reviews',
                axisLine: {
                    show: false
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#666',
                    formatter: (value) => {
                        if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
                        return value.toString();
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#f0f0f0',
                        type: 'dashed'
                    }
                }
            },
            series: [
                {
                    name: "Review Count",
                    type: "bar",
                    data: ratingData,
                    itemStyle: {
                        color: (params) => {
                            const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6'];
                            return colors[params.dataIndex] || '#9ca3af';
                        },
                        borderRadius: [4, 4, 0, 0]
                    },
                    label: {
                        show: true,
                        position: 'top',
                        formatter: (params) => {
                            const percentage = totalCount > 0 ? ((params.value / totalCount) * 100).toFixed(1) : 0;
                            return `${params.value}\n(${percentage}%)`;
                        },
                        fontSize: 11,
                        color: '#666'
                    },
                    barWidth: '60%'
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
    }, [data]);

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] min-h-[300px]">
            {!targetAirline ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        ✈️ Please search for an airline to view rating distribution
                    </div>
                </div>
            ) : loading ? (
                <div className="flex items-center justify-center h-full">
                    <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                </div>
            ) : !data || !Array.isArray(data) || data.length === 0 || data.every(item => item.count === 0) ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        {!data || !Array.isArray(data) 
                            ? "😢 No rating distribution data available"
                            : "🔍 Filter conditions too narrow or no rating field"}
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 pt-4 text-xl font-semibold">Rating Distribution (1-5)</div>
                    <CardContent className="flex flex-1 min-h-[250px]">
                        <div ref={chartRef} className="w-full h-full" />
                    </CardContent>
                </>
            )}
        </Card>
    );
}

