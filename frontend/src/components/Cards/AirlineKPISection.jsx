import { Card, CardContent } from "@/components/ui/card";
import React, { useMemo } from "react";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export const AirlineKPISection = () => {
    const targetAirline = useContext((state) => state.targetAirline);
    
    const url = useMemo(() => {
        if (!targetAirline) return null;
        return `/api/airlines/${encodeURIComponent(targetAirline)}/kpis`;
    }, [targetAirline]);
    
    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    const formatTrend = (value) => {
        if (value > 0) {
            return { icon: TrendingUp, color: 'text-green-600', text: `+${value.toFixed(1)}` };
        } else if (value < 0) {
            return { icon: TrendingDown, color: 'text-red-600', text: value.toFixed(1) };
        } else {
            return { icon: Minus, color: 'text-gray-500', text: '0.0' };
        }
    };

    const formatPercentage = (value) => {
        return `${(value * 100).toFixed(1)}%`;
    };

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] min-h-[300px]">
            {!targetAirline ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        ✈️ Please search for an airline to view KPIs
                    </div>
                </div>
            ) : loading ? (
                <div className="flex items-center justify-center h-full">
                    <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                </div>
            ) : !data ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        😢 No KPI data available
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 pt-4 text-xl font-semibold">Airline KPIs</div>
                    <CardContent className="grid grid-cols-3 gap-4 p-6">
                        {/* Review Count */}
                        <div className="bg-[#e2f4ff] rounded-2xl p-4 flex flex-col">
                            <div className="text-sm font-medium text-gray-500 mb-2">Review Count</div>
                            <div className="text-2xl font-bold text-[#0095ff]">{data.review_count?.toLocaleString() || 0}</div>
                        </div>

                        {/* Average Rating */}
                        <div className="bg-[#fff4de] rounded-2xl p-4 flex flex-col">
                            <div className="text-sm font-medium text-gray-500 mb-2">Avg Rating</div>
                            <div className="flex items-center gap-2">
                                <div className="text-2xl font-bold text-[#ff947a]">{data.avg_rating?.toFixed(1) || 0.0}</div>
                                <span className="text-sm text-gray-500">/ 10</span>
                            </div>
                        </div>

                        {/* Median Rating */}
                        <div className="bg-[#e2fff3] rounded-2xl p-4 flex flex-col">
                            <div className="text-sm font-medium text-gray-500 mb-2">Median Rating</div>
                            <div className="flex items-center gap-2">
                                <div className="text-2xl font-bold text-[#3cd856]">{data.median_rating?.toFixed(1) || 0.0}</div>
                                <span className="text-sm text-gray-500">/ 10</span>
                            </div>
                        </div>

                        {/* Rating Std Dev */}
                        <div className="bg-[#fbf1ff] rounded-2xl p-4 flex flex-col">
                            <div className="text-sm font-medium text-gray-500 mb-2">Rating Std Dev</div>
                            <div className="text-2xl font-bold text-[#a700ff]">{data.rating_std?.toFixed(2) || 0.0}</div>
                        </div>

                        {/* Positive Ratio */}
                        <div className="bg-[#e2fff3] rounded-2xl p-4 flex flex-col">
                            <div className="text-sm font-medium text-gray-500 mb-2">Positive Ratio</div>
                            <div className="text-2xl font-bold text-[#3cd856]">{formatPercentage(data.pos_ratio || 0)}</div>
                        </div>

                        {/* Negative Ratio */}
                        <div className="bg-[#ffe2e5] rounded-2xl p-4 flex flex-col">
                            <div className="text-sm font-medium text-gray-500 mb-2">Negative Ratio</div>
                            <div className="text-2xl font-bold text-[#fa5a7d]">{formatPercentage(data.neg_ratio || 0)}</div>
                        </div>

                        {/* Neutral Ratio */}
                        <div className="bg-[#f0f0f0] rounded-2xl p-4 flex flex-col">
                            <div className="text-sm font-medium text-gray-500 mb-2">Neutral Ratio</div>
                            <div className="text-2xl font-bold text-gray-600">{formatPercentage(data.neu_ratio || 0)}</div>
                        </div>

                        {/* Latest Month */}
                        <div className="bg-[#fff4de] rounded-2xl p-4 flex flex-col">
                            <div className="text-sm font-medium text-gray-500 mb-2">Latest Month</div>
                            <div className="text-xl font-bold text-[#ff947a]">{data.latest_month || 'N/A'}</div>
                        </div>

                        {/* MoM Change */}
                        <div className="bg-[#e2f4ff] rounded-2xl p-4 flex flex-col">
                            <div className="text-sm font-medium text-gray-500 mb-2">MoM Change</div>
                            <div className="flex items-center gap-2">
                                {(() => {
                                    const trend = formatTrend(data.mom_change_avg_rating || 0);
                                    const Icon = trend.icon;
                                    return (
                                        <>
                                            <Icon className={`w-5 h-5 ${trend.color}`} />
                                            <div className={`text-xl font-bold ${trend.color}`}>
                                                {trend.text}
                                            </div>
                                        </>
                                    );
                                })()}
                            </div>
                        </div>
                    </CardContent>
                </>
            )}
        </Card>
    );
};

export default AirlineKPISection;

