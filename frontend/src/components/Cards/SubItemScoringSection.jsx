import { Card, CardContent } from "@/components/ui/card";
import React, { useEffect, useRef, useMemo, useState } from "react";
import { init } from "echarts";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";

export default function SubItemScoringSection() {
    const chartRef = useRef(null);
    const targetAirline = useContext((state) => state.targetAirline);
    const [useSentiment, setUseSentiment] = useState(false);
    
    const url = useMemo(() => {
        if (!targetAirline) return null;
        return `/airlines/${encodeURIComponent(targetAirline)}/sub-item-scoring?use_sentiment=${useSentiment}`;
    }, [targetAirline, useSentiment]);
    
    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    useEffect(() => {
        if (!chartRef.current || !data) return;

        const chart = init(chartRef.current);

        const categories = [
            'Seat Comfort',
            'Cabin Staff & Service',
            'Food & Beverages',
            'Inflight Entertainment',
            'Ground Service',
            'Wifi Connectivity',
            'Value for Money'
        ];

        const targetData = categories.map(cat => data.target_airline[cat]);
        const avgData = categories.map(cat => data.average_score[cat]);

        const option = {
            tooltip: {
                trigger: 'item',
                formatter: (params) => {
                    return `${params.seriesName}<br/>${params.name}: ${params.value.toFixed(1)}`;
                }
            },
            legend: {
                data: ['Target Airline', 'Average Score'],
                bottom: '0%',
                textStyle: {
                    fontSize: 12
                },
                itemWidth: 10,
                itemHeight: 10,
                icon: 'circle'
            },
            radar: {
                indicator: [
                    { name: 'Seat Comfort', max: 5 },
                    { name: 'Cabin Staff & Service', max: 5 },
                    { name: 'Food & Beverages', max: 5 },
                    { name: 'Inflight Entertainment', max: 5 },
                    { name: 'Ground Service', max: 5 },
                    { name: 'Wifi Connectivity', max: 5 },
                    { name: 'Value for Money', max: 5 }
                ],
                center: ['50%', '55%'],
                radius: '70%',
                axisName: {
                    fontSize: 11,
                    color: '#666',
                    fontWeight: 'normal'
                },
                splitArea: {
                    show: true,
                    areaStyle: {
                        color: ['rgba(250, 250, 250, 0.3)', 'rgba(200, 200, 200, 0.1)']
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#e0e0e0',
                        type: 'dashed'
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: '#e0e0e0'
                    }
                }
            },
            series: [
                {
                    name: 'Target Airline',
                    type: 'radar',
                    data: [
                        {
                            value: targetData,
                            name: 'Target Airline',
                            areaStyle: {
                                color: 'rgba(0, 149, 255, 0.2)'
                            },
                            lineStyle: {
                                color: '#0095ff',
                                width: 2
                            },
                            itemStyle: {
                                color: '#0095ff'
                            }
                        }
                    ]
                },
                {
                    name: 'Average Score',
                    type: 'radar',
                    data: [
                        {
                            value: avgData,
                            name: 'Average Score',
                            areaStyle: {
                                color: 'rgba(0, 224, 150, 0.2)'
                            },
                            lineStyle: {
                                color: '#00e096',
                                width: 2
                            },
                            itemStyle: {
                                color: '#00e096'
                            }
                        }
                    ]
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
            // chartRef.current = null;
        };
    }, [data, useSentiment]);

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] min-h-[300px]">
            {!targetAirline ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        ✈️ Please search for an airline to view sub-item scoring
                    </div>
                </div>
            ) : loading ? (
                <div className="flex items-center justify-center h-full">
                    <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                </div>
            ) : !data ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        😢 No sub-item scoring data available
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 pt-4 flex items-center justify-between pr-6">
                        <div className="text-xl font-semibold">Sub-Item Scoring</div>
                        <div className="flex gap-2 items-center">
                            <Button
                                variant={!useSentiment ? 'default' : 'outline'}
                                size="sm"
                                onClick={() => setUseSentiment(false)}
                                className="h-8"
                            >
                                Rating Data
                            </Button>
                            <Button
                                variant={useSentiment ? 'default' : 'outline'}
                                size="sm"
                                onClick={() => setUseSentiment(true)}
                                className="h-8"
                            >
                                Sentiment
                            </Button>
                        </div>
                    </div>

                    <CardContent className="flex flex-1 min-h-[250px]">
                        <div ref={chartRef} className="w-full h-full" />
                    </CardContent>
                </>
            )}
        </Card>
    );
}
