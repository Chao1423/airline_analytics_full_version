import { Card, CardContent } from "@/components/ui/card";
import React, { useEffect, useRef, useMemo, useState } from "react";
import { init } from "echarts";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";

export default function SegmentRatingDistributionSection() {
    const chartRef = useRef(null);
    const targetAirline = useContext((state) => state.targetAirline);
    const [selectedSegment, setSelectedSegment] = useState('seatType');
    
    // Dynamic limits based on segment type
    // For country and aircraft, use stricter limits to prevent overcrowding
    const getSegmentLimit = (segment) => {
        if (segment === 'country' || segment === 'aircraft') {
            return 10; // Top 10 for segments with many values
        }
        // For seatType and typeOfTraveller, show more since there are fewer values
        return 15; // Top 15 for segments with fewer values
    };
    
    const limit = getSegmentLimit(selectedSegment);
    
    const url = useMemo(() => {
        if (!targetAirline) return null;
        return `/airlines/${encodeURIComponent(targetAirline)}/rating-distribution-by-segment?segment=${selectedSegment}&limit=${limit}`;
    }, [targetAirline, selectedSegment, limit]);
    
    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    const segmentOptions = [
        { value: 'seatType', label: 'Seat Type' },
        { value: 'typeOfTraveller', label: 'Type of Traveller' },
        { value: 'country', label: 'Country' },
        { value: 'aircraft', label: 'Aircraft' },
    ];

    useEffect(() => {
        if (!chartRef.current || !data || !Array.isArray(data) || data.length === 0) return;

        const chart = init(chartRef.current);

        // Prepare data for grouped bar chart
        const segments = data.map(item => item.segment);
        const ratings = [1, 2, 3, 4, 5];
        
        // Create series for each rating (grouped bars, not stacked)
        const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6'];
        
        const series = ratings.map((rating, ratingIndex) => {
            const ratingData = data.map(item => {
                const distItem = item.distribution.find(d => d.rating === rating);
                return distItem ? distItem.count : 0;
            });
            
            return {
                name: `Rating ${rating}`,
                type: 'bar',
                data: ratingData,
                itemStyle: {
                    color: colors[ratingIndex],
                    borderRadius: [4, 4, 0, 0]
                },
                label: {
                    show: true,
                    position: 'top',
                    formatter: (params) => {
                        return params.value > 0 ? params.value : '';
                    },
                    fontSize: 10,
                    color: '#666',
                    fontWeight: 'bold'
                },
                barWidth: '15%',
                barGap: '10%'
            };
        });

        // Calculate totals for tooltip
        const totals = segments.map((_, segIndex) => {
            return data[segIndex].distribution.reduce((sum, d) => sum + d.count, 0);
        });

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
                    let result = `${params[0].axisValue}<br/>`;
                    let total = 0;
                    params.forEach(param => {
                        const percentage = totals[param.dataIndex] > 0 ? ((param.value / totals[param.dataIndex]) * 100).toFixed(1) : 0;
                        result += `<span style="display:inline-block;margin-right:5px;border-radius:2px;width:10px;height:10px;background-color:${param.color};"></span>${param.seriesName}: ${param.value} (${percentage}%)<br/>`;
                        total += param.value;
                    });
                    result += `<b>Total: ${total}</b>`;
                    return result;
                }
            },
            legend: {
                data: ratings.map(r => `Rating ${r}`),
                bottom: '0%',
                textStyle: {
                    fontSize: 12
                },
                itemWidth: 10,
                itemHeight: 10
            },
            xAxis: {
                type: "category",
                data: segments,
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
                    rotate: segments.some(s => s && s.length > 10) ? -15 : 0,
                    interval: 0
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
            series: series
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
            ) : !data || !Array.isArray(data) || data.length === 0 || data.every(item => item.distribution.every(d => d.count === 0)) ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        {!data || !Array.isArray(data) 
                            ? "😢 No rating distribution data available"
                            : "🔍 Filter conditions too narrow or no rating field"}
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 pt-4 flex items-center justify-between pr-6">
                        <div className="flex flex-col">
                            <div className="text-xl font-semibold">Rating Distribution by Segment</div>
                            {(selectedSegment === 'country' || selectedSegment === 'aircraft') && (
                                <div className="text-xs text-gray-500 mt-1">
                                    Showing top {limit} segments by review count
                                </div>
                            )}
                        </div>
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="outline" className="w-[180px] justify-between h-9">
                                    {segmentOptions.find(opt => opt.value === selectedSegment)?.label || 'Select segment'}
                                    <ChevronDown className="ml-2 h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                {segmentOptions.map(option => (
                                    <DropdownMenuItem 
                                        key={option.value} 
                                        onClick={() => setSelectedSegment(option.value)}
                                        className={selectedSegment === option.value ? 'bg-accent' : ''}
                                    >
                                        {option.label}
                                    </DropdownMenuItem>
                                ))}
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                    <CardContent className="flex flex-1 min-h-[250px]">
                        <div ref={chartRef} className="w-full h-full" />
                    </CardContent>
                </>
            )}
        </Card>
    );
}

