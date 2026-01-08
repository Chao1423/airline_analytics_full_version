import { Card, CardContent } from "@/components/ui/card";
import React, { useEffect, useRef, useMemo } from "react";
import { init, registerMap } from "echarts";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";

export const AirlineMappingSection = () => {
    const chartRef = useRef(null);
    const targetAirline = useContext((state) => state.targetAirline);
    
    const url = useMemo(() => {
        if (!targetAirline) return null;
        return `/airlines/${encodeURIComponent(targetAirline)}/city-distribution`;
    }, [targetAirline]);

    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    useEffect(() => {
        if (!chartRef.current || !data || data.length === 0) return;

        const chart = init(chartRef.current, null, {
            renderer: 'canvas',
            width: 'auto',
            height: 'auto'
        });
        chart.showLoading();

        fetch('/world.json')
            .then(response => response.json())
            .then(geoJSON => {
                registerMap('world', geoJSON);

                const option = {
                    tooltip: {
                        trigger: 'item',
                        formatter: (params) => {
                            if (params.componentSubType === 'scatter') {
                                return `${params.name}<br/>Routes: ${params.value[2]}`;
                            }
                            return params.name;
                        }
                    },
                    geo: {
                        map: 'world',
                        left: '5%',
                        right: '5%',
                        top: '10%',
                        bottom: '10%',
                        roam: true,
                        zoom: 1,
                        center: [10, 15],
                        itemStyle: {
                            areaColor: '#e5e7eb',
                            borderColor: '#fff',
                            borderWidth: 1.5
                        },
                        emphasis: {
                            itemStyle: {
                                areaColor: '#d1d5db'
                            }
                        },
                        layoutCenter: ['50%', '50%'],
                        layoutSize: '90%'
                    },
                    series: [
                        {
                            type: 'scatter',
                            coordinateSystem: 'geo',
                            data: data,
                            symbolSize: (val) => {
                                return Math.sqrt(val[2]) * 3.5;
                            },
                            itemStyle: {
                                opacity: 0.8
                            },
                            emphasis: {
                                scale: true,
                                scaleSize: 15
                            }
                        }
                    ]
                };

                chart.setOption(option);
                chart.hideLoading();
            })
            .catch(err => {
                console.error('Failed to load map:', err);
                chart.hideLoading();
            });

        const resizeObserver = new ResizeObserver(() => {
            chart.resize();
        });

        resizeObserver.observe(chartRef.current);

        return () => {
            resizeObserver.disconnect();
            chart.dispose();
            // chartRef.current = null;
        };
    }, [data]);

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] min-h-[500px]">
            {!targetAirline ? (
                <div className="flex items-center justify-center h-full min-h-[500px]">
                    <div className="text-xl font-semibold text-center">
                        ✈️ Please search for an airline to view city distribution
                    </div>
                </div>
            ) : loading ? (
                <div className="flex items-center justify-center h-full min-h-[500px]">
                    <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                </div>
            ) : !data || data.length === 0 ? (
                <div className="flex items-center justify-center h-full min-h-[500px]">
                    <div className="text-xl font-semibold text-center">
                        😢 No city distribution data available
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 pt-4 text-xl font-semibold">Airline Mapping</div>

                    <CardContent className="p-0" style={{ height: '450px' }}>
                        <div ref={chartRef} style={{ width: '100%', height: '100%', minHeight: '450px' }} />
                    </CardContent>
                </>
            )}
        </Card>
    );
};

export default AirlineMappingSection