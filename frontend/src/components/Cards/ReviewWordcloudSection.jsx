import { Card, CardContent } from "@/components/ui/card";
import React, { useEffect, useRef, useMemo } from "react";
import { init } from "echarts";
import "echarts-wordcloud";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";

export default function ReviewWordcloudSection() {
    const posChartRef = useRef(null);
    const negChartRef = useRef(null);
    const targetAirline = useContext((state) => state.targetAirline);

    const url = useMemo(() => {
        if (!targetAirline) return null;
        return `/airlines/${encodeURIComponent(targetAirline)}/wordcloud-data`;
    }, [targetAirline]);

    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    const renderWordCloud = (chartRef, words, colorShades) => {
        const myChart = init(chartRef.current);
        
        const option = {
            tooltip: {
                show: true,
                formatter: (params) => `${params.name}<br>Score: ${params.value}`,
            },
            series: [{
                type: "wordCloud",
                shape: "circle",
                left: 0,
                right: 0,
                width: '100%',
                height: '100%',
                sizeRange: [14, 50],
                rotationRange: [-45, 45],
                gridSize: 8,
                textStyle: {
                    fontFamily: "sans-serif",
                    fontWeight: "bold",
                    color: () => {
                        return colorShades[Math.floor(Math.random() * colorShades.length)];
                    },
                },
                data: words,
            }],
        };
        
        myChart.setOption(option);
        
        const observer = new ResizeObserver(() => {
            myChart.resize();
        });
        observer.observe(chartRef.current);
        chartRef.current._observer = observer;
    };
    
    useEffect(() => {
        if (!data) return;
    
        const posWords = Object.entries(data.pos_dict || {}).map(([word, metrics]) => ({
            name: word,
            value: Math.abs(metrics.score) || 1,
        }));
    
        const negWords = Object.entries(data.neg_dict || {}).map(([word, metrics]) => ({
            name: word,
            value: Math.abs(metrics.score) || 1,
        }));
    
        const greenShades = ['#10b981', '#059669', '#34d399', '#6ee7b7', '#22c55e', '#16a34a'];
        const redShades = ['#ef4444', '#dc2626', '#f87171', '#fca5a5', '#e11d48', '#be123c'];

        if (posChartRef.current && negChartRef.current) {
            renderWordCloud(posChartRef, posWords, greenShades);
            renderWordCloud(negChartRef, negWords, redShades);
        }
    }, [data]);

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80]">
            {!targetAirline ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        ✈️ Please search for an airline to view wordcloud
                    </div>
                </div>
            ) : loading ? (
                <div className="flex items-center justify-center h-full">
                    <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                </div>
            ) : !data ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        😢 No wordcloud data available
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 text-xl font-semibold">Review WorldCloud</div>

                    <CardContent className="flex flex-1 justify-between gap-4 mx-2">
                        <div className="flex flex-1 flex-col">
                            <div ref={posChartRef} className="w-full h-full" />
                            <div className="flex items-center justify-center gap-2 mt-3">
                                <span className="w-2.5 h-2.5 rounded-full bg-green-600"></span>
                                <span className="text-xs font-normal">Positive Sentiment</span>
                            </div>
                        </div>

                        <div className="flex flex-1 flex-col">
                            <div ref={negChartRef} className="w-full h-full" />
                            <div className="flex items-center justify-center gap-2 mt-3">
                                <span className="w-2.5 h-2.5 rounded-full bg-red-600"></span>
                                <span className="text-xs font-normal">Negative Sentiment</span>
                            </div>
                        </div>

                        <div className="flex flex-col gap-4 justify-center">
                            <div className="flex justify-between gap-4">
                                <div>
                                    <div className="text-base font-medium text-gray-500">Positive Score</div>
                                    <div className="text-sm font-medium text-gray-500">Word Count</div>
                                </div>
                                <div className="text-right">
                                    <div className="text-lg font-semibold text-green-600">{data?.pos_score?.toLocaleString() || '0'}</div>
                                    <div className="text-sm font-medium text-gray-500">{data?.pos_count || 0}</div>
                                </div>
                            </div>

                            <div className="flex justify-between gap-4">
                                <div>
                                    <div className="text-base font-medium text-gray-500">Negative Score</div>
                                    <div className="text-sm font-medium text-gray-500">Word Count</div>
                                </div>
                                <div className="text-right">
                                    <div className="text-lg font-semibold text-red-600">{data?.neg_score?.toLocaleString() || '0'}</div>
                                    <div className="text-sm font-medium text-gray-500">{data?.neg_count || 0}</div>
                                </div>
                            </div>

                            <div className="flex justify-between gap-4">
                                <div>
                                    <div className="text-base font-medium text-gray-500">Overall Score</div>
                                    <div className="text-sm font-medium text-gray-500">Word Count</div>
                                </div>
                                <div className="text-right">
                                    <div className={`text-lg font-semibold ${(data?.overall_score || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>{data?.overall_score?.toLocaleString() || '0'}</div>
                                    <div className="text-sm font-medium text-gray-500">{data?.overall_count || 0}</div>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </>
            )}
        </Card>
    );
}
