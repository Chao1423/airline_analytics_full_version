import { Card, CardContent } from "@/components/ui/card";
import React, { useEffect, useRef, useMemo } from "react";
import { init } from "echarts";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";

export default function RatingDistributionSection() {
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
        if (!chartRef.current || !data) return;

        const chart = init(chartRef.current);

        const option = {
            grid: {
                top: '10%',
                left: '3%',
                right: '4%',
                bottom: '22%',
                containLabel: true
            },
            tooltip: {
                trigger: "axis",
                axisPointer: {
                    type: 'line'
                }
            },
            legend: {
                data: ['Seat Comfort', 'Cabin & Staff Service', 'Food & Beverages', 
                       'Inflight Entertainment', 'Ground Service', 'Wifi Connectivity', 'Value For Money'],
                bottom: '0%',
                textStyle: {
                    fontSize: 12
                },
                itemWidth: 10,
                itemHeight: 10
            },
            xAxis: {
                type: "category",
                boundaryGap: false,
                data: ['0', '1', '2', '3', '4', '5'],
                axisLine: {
                    lineStyle: {
                        color: '#e0e0e0'
                    }
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#999'
                }
            },
            yAxis: {
                type: "value",
                min: 0,
                max: 1,
                interval: 0.2,
                axisLine: {
                    show: false
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#999'
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
                    name: "Seat Comfort",
                    type: "line",
                    smooth: true,
                    data: data["Seat Comfort"],
                    lineStyle: { width: 3, color: '#9b59b6' },
                    itemStyle: { color: '#9b59b6' },
                    showSymbol: false
                },
                {
                    name: "Cabin & Staff Service",
                    type: "line",
                    smooth: true,
                    data: data["Cabin & Staff Service"],
                    lineStyle: { width: 3, color: '#e74c3c' },
                    itemStyle: { color: '#e74c3c' },
                    showSymbol: false
                },
                {
                    name: "Food & Beverages",
                    type: "line",
                    smooth: true,
                    data: data["Food & Beverages"],
                    lineStyle: { width: 3, color: '#2ecc71' },
                    itemStyle: { color: '#2ecc71' },
                    showSymbol: false
                },
                {
                    name: "Inflight Entertainment",
                    type: "line",
                    smooth: true,
                    data: data["Inflight Entertainment"],
                    lineStyle: { width: 3, color: '#3498db' },
                    itemStyle: { color: '#3498db' },
                    showSymbol: false
                },
                {
                    name: "Ground Service",
                    type: "line",
                    smooth: true,
                    data: data["Ground Service"],
                    lineStyle: { width: 3, color: '#f39c12' },
                    itemStyle: { color: '#f39c12' },
                    showSymbol: false
                },
                {
                    name: "Wifi Connectivity",
                    type: "line",
                    smooth: true,
                    data: data["Wifi Connectivity"],
                    lineStyle: { width: 3, color: '#1abc9c' },
                    itemStyle: { color: '#1abc9c' },
                    showSymbol: false
                },
                {
                    name: "Value For Money",
                    type: "line",
                    smooth: true,
                    data: data["Value For Money"],
                    lineStyle: { width: 3, color: '#e67e22' },
                    itemStyle: { color: '#e67e22' },
                    showSymbol: false
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
            ) : !data ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        😢 No rating distribution data available
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 text-xl font-semibold">Rating Distribution</div>

                    <CardContent className="flex flex-1 min-h-[250px]">
                        <div ref={chartRef} className="w-full h-full" />
                    </CardContent>
                </>
            )}
        </Card>
    );
}
