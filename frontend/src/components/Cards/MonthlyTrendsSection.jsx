import { Card, CardContent } from "@/components/ui/card";
import React, { useEffect, useRef, useMemo, useState } from "react";
import { init } from "echarts";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";

export default function MonthlyTrendsSection() {
    const chartRef = useRef(null);
    const targetAirline = useContext((state) => state.targetAirline);
    const [metric, setMetric] = useState('avg_rating'); // 'avg_rating' or 'sentiment_mean'
    
    const url = useMemo(() => {
        if (!targetAirline) return null;
        return `/api/airlines/${encodeURIComponent(targetAirline)}/monthly-trends`;
    }, [targetAirline]);
    
    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    useEffect(() => {
        if (!chartRef.current || !data || !Array.isArray(data) || data.length === 0) return;

        const chart = init(chartRef.current);

        // Prepare data
        const months = data.map(item => item.month);
        const avgRatings = data.map(item => item.avg_rating || 0);
        const sentimentMeans = data.map(item => item.sentiment_mean || null);

        const option = {
            grid: {
                top: '15%',
                left: '10%',
                right: '10%',
                bottom: '15%',
                containLabel: true
            },
            tooltip: {
                trigger: "axis",
                axisPointer: {
                    type: 'cross'
                },
                formatter: (params) => {
                    const param = params[0];
                    const month = param.axisValue;
                    const monthData = data.find(d => d.month === month);
                    
                    let result = `${month}<br/>`;
                    if (param.value !== null && param.value !== undefined && !isNaN(param.value)) {
                        result += `<span style="display:inline-block;margin-right:5px;border-radius:2px;width:10px;height:10px;background-color:${param.color};"></span>${param.seriesName}: ${param.value.toFixed(2)}<br/>`;
                    } else {
                        result += `<span style="display:inline-block;margin-right:5px;border-radius:2px;width:10px;height:10px;background-color:${param.color};"></span>${param.seriesName}: N/A<br/>`;
                    }
                    
                    if (monthData) {
                        result += `Review Count: ${monthData.review_count}<br/>`;
                        if (monthData.destination_topN && monthData.destination_topN.length > 0) {
                            result += `Top Destinations: ${monthData.destination_topN.slice(0, 3).map(d => d.destination).join(', ')}`;
                        }
                    }
                    
                    return result;
                }
            },
            legend: {
                data: [metric === 'avg_rating' ? 'Average Rating' : 'Sentiment Mean'],
                bottom: '0%',
                textStyle: {
                    fontSize: 12
                }
            },
            xAxis: {
                type: "category",
                data: months,
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
                    fontSize: 11,
                    rotate: months.length > 12 ? -45 : 0,
                    interval: months.length > 24 ? 'auto' : 0
                }
            },
            yAxis: {
                type: "value",
                name: metric === 'avg_rating' ? 'Average Rating' : 'Sentiment Mean',
                axisLine: {
                    show: false
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#666',
                    formatter: (value) => {
                        return value.toFixed(1);
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
                    name: metric === 'avg_rating' ? 'Average Rating' : 'Sentiment Mean',
                    type: 'line',
                    smooth: true,
                    data: metric === 'avg_rating' ? avgRatings : sentimentMeans,
                    itemStyle: {
                        color: '#5D5FEF'
                    },
                    lineStyle: {
                        width: 3,
                        color: '#5D5FEF'
                    },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                { offset: 0, color: 'rgba(93, 95, 239, 0.3)' },
                                { offset: 1, color: 'rgba(93, 95, 239, 0.05)' }
                            ]
                        }
                    },
                    symbol: 'circle',
                    symbolSize: 6,
                    label: {
                        show: false
                    }
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
    }, [data, metric]);

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] min-h-[300px]">
            {!targetAirline ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        ✈️ Please search for an airline to view monthly trends
                    </div>
                </div>
            ) : loading ? (
                <div className="flex items-center justify-center h-full">
                    <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                </div>
            ) : !data || !Array.isArray(data) || data.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        😢 No monthly trends data available
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 pt-4 flex items-center justify-between pr-6">
                        <div className="text-xl font-semibold">Monthly Trends</div>
                        <div className="flex gap-2 items-center">
                            <Button
                                variant={metric === 'avg_rating' ? 'default' : 'outline'}
                                size="sm"
                                onClick={() => setMetric('avg_rating')}
                                className="h-8"
                            >
                                Avg Rating
                            </Button>
                            <Button
                                variant={metric === 'sentiment_mean' ? 'default' : 'outline'}
                                size="sm"
                                onClick={() => setMetric('sentiment_mean')}
                                className="h-8"
                            >
                                Sentiment
                            </Button>
                            {metric === 'sentiment_mean' && data.every(item => !item.sentiment_mean) && (
                                <span className="text-xs text-gray-500 ml-2">
                                    (Processing...)
                                </span>
                            )}
                        </div>
                    </div>
                    <CardContent className="flex flex-1 min-h-[250px]">
                        {metric === 'sentiment_mean' && data.every(item => !item.sentiment_mean) ? (
                            <div className="flex items-center justify-center w-full h-full">
                                <div className="text-center">
                                    <div className="text-lg font-semibold text-gray-600 mb-2">
                                        No sentiment data available yet
                                    </div>
                                    <div className="text-sm text-gray-500">
                                        The sentiment analysis pipeline is processing reviews.
                                        <br />
                                        Data will appear here as reviews are processed.
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div ref={chartRef} className="w-full h-full" />
                        )}
                    </CardContent>
                </>
            )}
        </Card>
    );
}

