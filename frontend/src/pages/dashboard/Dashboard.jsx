import { AirlineKeyDataSection } from "../../components/Cards/AirlineKeyDataSection";
import { AirlineMappingSection } from "../../components/Cards/AirlineMappingSection";
import FeatureImportanceSection from "../../components/Cards/FeatureImportanceSection";
import RatingDistributionSection from "../../components/Cards/RatingDistributionSection";
import RatingDistributionBarSection from "../../components/Cards/RatingDistributionBarSection";
import SegmentRatingDistributionSection from "../../components/Cards/SegmentRatingDistributionSection";
import ReviewWordcloudSection from "../../components/Cards/ReviewWordcloudSection";
import SubItemScoringSection from "../../components/Cards/SubItemScoringSection";
import TopRatedAirlinesSection from "../../components/Cards/TopRatedAirlinesSection";
import AirlineKPISection from "../../components/Cards/AirlineKPISection";
import MonthlyTrendsSection from "../../components/Cards/MonthlyTrendsSection";
import TopTopicsSection from "../../components/Cards/TopTopicsSection";
import { useMemo } from "react";
import useContext from "../../zustand/useContext";
import useQuery from "../../hooks/useQuery";

const Dashboard = () => {
    const targetAirline = useContext((state) => state.targetAirline);
    
    // 预加载 review 数据（当选择航空公司时）
    // 这样在 Review Data 页面打开时可以直接显示数据，无需等待加载
    const reviewUrl = useMemo(() => {
        if (!targetAirline) return null;
        return `/api/reviews/search?airline_name=${encodeURIComponent(targetAirline)}&page=1&page_size=20`;
    }, [targetAirline]);
    
    // 使用 useQuery 预加载数据（不显示 loading，只缓存）
    // 这个调用不会影响 Dashboard 的渲染，只是后台预加载数据
    useQuery(reviewUrl, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
        enabled: !!targetAirline, // 只在有航空公司时启用
    });
    
    return (
        <div className="flex flex-col gap-2 my-2 mr-2 w-full">

            <div className="grid grid-cols-[5fr_4fr] gap-2">
                <AirlineKPISection />
                <TopRatedAirlinesSection />
            </div>

            <div className="grid grid-cols-[5fr_4fr] gap-2">
                <MonthlyTrendsSection />
                <TopTopicsSection />                
            </div>

            <div className="grid grid-cols-[4fr_5fr] gap-2">
                <RatingDistributionBarSection />
                <SegmentRatingDistributionSection />

            </div>

            <div className="grid grid-cols-[4fr_5fr] gap-2">
                <SubItemScoringSection />
                <ReviewWordcloudSection />
            </div>

            <div className="w-full">
                <AirlineMappingSection />
            </div>

        </div>
    );
};

export default Dashboard;
