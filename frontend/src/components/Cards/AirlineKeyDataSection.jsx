import { Card, CardContent } from "@/components/ui/card";
import { FaUtensils, FaUsers, FaTrophy, FaWifi } from "react-icons/fa";
import React, { useMemo } from "react";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";

export const AirlineKeyDataSection = () => {
    const targetAirline = useContext((state) => state.targetAirline);
    
    const url = useMemo(() => {
        if (!targetAirline) return null;
        return `/airlines/${encodeURIComponent(targetAirline)}/key-data`;
    }, [targetAirline]);
    
    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] min-h-[300px]">
            {!targetAirline ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        ✈️ Please search for an airline to view key data
                    </div>
                </div>
            ) : loading ? (
                <div className="flex items-center justify-center h-full">
                    <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                </div>
            ) : !data ? (
                <div className="flex items-center justify-center h-full">
                    <div className="text-xl font-semibold text-center">
                        😢 No key data available
                    </div>
                </div>
            ) : (
                <>
                    <div className="pl-6 text-xl font-semibold">Airline Key Data</div>
                        
                    <CardContent className="flex justify-between">
                        <div className="flex flex-col gap-4 w-[23%]">
                            <div className="bg-[#ffe2e5] rounded-2xl p-4 flex flex-col">
                                <div className="bg-[#fa5a7d] rounded-[20px] w-10 h-10 flex items-center justify-center mb-4">
                                    <FaUtensils className="w-6 h-6 text-white" />
                                </div>
                                <div className="text-lg font-semibold mb-2">{data.top_rated_item?.score}</div>
                                <div className="text-sm font-medium text-gray-500 mb-2">Top-Rated Item</div>
                                <div className="text-[#4079ED] text-xs font-medium">{data.top_rated_item?.category}</div>
                            </div>

                            <div className="flex flex-col ml-2">
                                <div className="text-sm font-medium text-gray-500 mb-2">Preferred Seat Type</div>
                                <div className="text-[#4079ED] text-xs font-medium">{data.preferred_seat_type}</div>
                            </div>
                        </div>


                        <div className="flex flex-col gap-4 w-[23%]">
                            <div className="bg-[#fff4de] rounded-2xl p-4 flex flex-col">
                                <div className="bg-[#ff947a] rounded-[20px] w-10 h-10 flex items-center justify-center mb-4">
                                    <FaUsers className="w-6 h-6 text-white" />
                                </div>
                                <div className="text-lg font-semibold mb-2">{data.total_rated_users?.count}</div>
                                <div className="text-sm font-medium text-gray-500 mb-2">Total Rated Users</div>
                                <div className="text-[#4079ED] text-xs font-medium">Medium Number: {data.total_rated_users?.medium_number}</div>
                            </div>

                            <div className="flex flex-col ml-2">
                                <div className="text-sm font-medium text-gray-500 mb-2">Preferred Route</div>
                                <div className="text-[#4079ED] text-xs font-medium">{data.preferred_route}</div>
                            </div>
                        </div>


                        <div className="flex flex-col gap-4 w-[23%]">
                            <div className="bg-[#e2fff3] rounded-2xl p-4 flex flex-col">
                                <div className="bg-[#3cd856] rounded-[20px] w-10 h-10 flex items-center justify-center mb-4">
                                    <FaTrophy className="w-6 h-6 text-white" />
                                </div>
                                <div className="text-lg font-semibold mb-2">{data.overall_score?.score}</div>
                                <div className="text-sm font-medium text-gray-500 mb-2">Overall Score</div>
                                <div className="text-[#4079ED] text-xs font-medium">{data.overall_score?.rank}</div>
                            </div>

                            <div className="flex flex-col ml-2">
                                <div className="text-sm font-medium text-gray-500 mb-2">Review Time</div>
                                <div className="text-[#4079ED] text-xs font-medium">{data.review_time?.start} to {data.review_time?.end}</div>
                            </div>
                        </div>


                        <div className="flex flex-col gap-4 w-[23%]">
                            <div className="bg-[#fbf1ff] rounded-2xl p-4 flex flex-col">
                                <div className="bg-[#a700ff] rounded-[20px] w-10 h-10 flex items-center justify-center mb-4">
                                    <FaWifi className="w-6 h-6 text-white" />
                                </div>
                                <div className="text-lg font-semibold mb-2">{data.lowest_rated_item?.score}</div>
                                <div className="text-sm font-medium text-gray-500 mb-2">Lowest-Rated Item</div>
                                <div className="text-[#4079ED] text-xs font-medium">{data.lowest_rated_item?.category}</div>
                            </div>

                            <div className="flex flex-col ml-2">
                                <div className="text-sm font-medium text-gray-500 mb-2">Flown Time</div>
                                <div className="text-[#4079ED] text-xs font-medium">{data.flown_time?.start} to {data.flown_time?.end}</div>
                            </div>
                        </div>
                    </CardContent>
                </>
            )}
        </Card>
    );
};

export default AirlineKeyDataSection;
