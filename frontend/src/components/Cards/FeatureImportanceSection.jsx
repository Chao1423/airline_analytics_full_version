import { Card, CardContent } from "@/components/ui/card";
import React, { useEffect, useRef, useMemo } from "react";
import { init } from "echarts";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";

export default function FeatureImportanceSection() {
    const chartRef = useRef(null);
    const targetAirline = useContext((state) => state.targetAirline);

    const url = useMemo(() => {
        if (!targetAirline) return null;
        return `/api/airlines/${encodeURIComponent(targetAirline)}/feature-importance`;
    }, [targetAirline]);

    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    useEffect(() => {
        if (!chartRef.current || !data || !data.topics || data.topics.length === 0) return;

        const chart = init(chartRef.current);

        // 准备数据：按绝对值排序
        const topics = [...data.topics].sort((a, b) => Math.abs(b.coef) - Math.abs(a.coef));
        
        const topicLabels = topics.map(t => t.topic_label);
        const coefficients = topics.map(t => t.coef);
        const ciLow = topics.map(t => t.ci_low);
        const ciHigh = topics.map(t => t.ci_high);

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                },
                formatter: (params) => {
                    const param = params[0];
                    const index = param.dataIndex;
                    const topic = topics[index];
                    let result = `${topic.topic_label}<br/>`;
                    result += `Coefficient: ${topic.coef.toFixed(4)}<br/>`;
                    result += `95% CI: [${topic.ci_low.toFixed(4)}, ${topic.ci_high.toFixed(4)}]<br/>`;
                    result += `P-value: ${topic.p_value.toFixed(4)}<br/>`;
                    result += `Mean Share: ${(topic.mean_topic_share * 100).toFixed(2)}%`;
                    
                    // 解释
                    if (topic.coef > 0) {
                        result += `<br/><span style="color: #10b981;">Positive: Increases ratings</span>`;
                    } else {
                        result += `<br/><span style="color: #ef4444;">Negative: Decreases ratings</span>`;
                    }
                    
                    return result;
                }
            },
            grid: {
                top: '10%',
                left: '25%',
                right: '10%',
                bottom: '15%',
                containLabel: false
            },
            xAxis: {
                type: 'value',
                name: 'Coefficient',
                nameLocation: 'middle',
                nameGap: 30,
                axisLine: {
                    show: true,
                    lineStyle: {
                        color: '#e0e0e0'
                    }
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#666',
                    formatter: (value) => value.toFixed(2)
                },
                splitLine: {
                    lineStyle: {
                        color: '#f0f0f0',
                        type: 'dashed'
                    }
                }
            },
            yAxis: {
                type: 'category',
                data: topicLabels,
                axisLine: {
                    show: false
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#666',
                    fontSize: 11
                }
            },
            series: [
                {
                    name: 'Coefficient',
                    type: 'bar',
                    data: coefficients.map((coef, index) => ({
                        value: coef,
                        itemStyle: {
                            color: coef >= 0 ? '#10b981' : '#ef4444'
                        }
                    })),
                    barWidth: '50%',
                    label: {
                        show: true,
                        position: 'right',
                        formatter: (params) => {
                            return params.value.toFixed(3);
                        },
                        color: '#333',
                        fontSize: 11
                    },
                    markLine: {
                        silent: true,
                        lineStyle: {
                            color: '#999',
                            type: 'dashed',
                            width: 1
                        },
                        data: [
                            { xAxis: 0 }
                        ]
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
    }, [data]);

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] min-h-[300px]">
            {!targetAirline ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        ✈️ Please search for an airline to view feature importance
                    </div>
                </div>
            ) : loading ? (
                <div className="flex items-center justify-center h-full">
                    <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                </div>
            ) : !data || !data.topics || data.topics.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                        <div className="text-xl font-semibold mb-2">
                        😢 No feature importance data available
                        </div>
                        <div className="text-sm text-gray-500">
                            Topic analysis requires reviews_topics table with sufficient data (30+ reviews)
                        </div>
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 pt-4 text-xl font-semibold">Feature Importance</div>
                    {data.model_r_squared !== null && data.sample_size !== null && (
                        <div className="pl-6 pt-2 text-xs text-gray-500">
                            R² = {data.model_r_squared.toFixed(3)} | Sample Size = {data.sample_size}
                        </div>
                    )}
                    <CardContent className="flex flex-1 min-h-[250px]">
                        <div ref={chartRef} className="w-full h-full" />
                    </CardContent>
                    <div className="pl-6 pb-4 text-xs text-gray-500 italic">
                        Negative coefficients indicate topics that reduce customer ratings.
                    </div>
                </>
            )}
        </Card>
    );
}
