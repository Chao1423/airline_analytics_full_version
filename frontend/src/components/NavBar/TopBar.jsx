import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { RotateCcw, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button"
import React, { useState, useMemo } from "react";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";

export const TopBar = () => {
    const [searchInput, setSearchInput] = useState("");
    const setTargetAirline = useContext((state) => state.setTargetAirline);

    const targetAirline = useContext((state) => state.targetAirline);

    const url = useMemo(() => {
        if (!targetAirline) return null;
        return `/airlines/${encodeURIComponent(targetAirline)}/info`;
    }, [targetAirline]);
    
    const { data, loading } = useQuery(url, {
        cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
        staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    const handleSearchSubmit = () => {
        const trimmedInput = searchInput.trim();
        if (trimmedInput && !loading) {
            setTargetAirline(trimmedInput);
            setSearchInput("");
        }
    };
    
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !loading) {
            handleSearchSubmit();
        }
    };

    const handleReset = () => {
        setTargetAirline("");
        setSearchInput("");
    };

    return (
        <div className="flex h-[80px] items-center justify-end z-100 pr-[30px] w-full bg-white 
            rounded-lg border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80]">
            
            <div className="flex justify-between items-center gap-[24px]">

                {targetAirline && data && (
                    <div className="flex justify-between items-center gap-[12px]">
                        <Avatar className="w-[60px] h-[60px] overflow-hidden rounded-full bg-white">
                            <AvatarImage src={data?.image} className="object-contain" />
                            <AvatarFallback>Nan</AvatarFallback>
                        </Avatar>

                        <span className="font-semibold text-xl">{data?.name}</span>
                                
                        <div onClick={loading ? undefined : handleReset}
                            className="bg-[#5D5FEF] hover:bg-[#4C4ED0] cursor-pointer h-[28px] w-[28px] 
                            flex items-center justify-center rounded-full text-white">
                            <RotateCcw className="h-[16px] w-[16px]" />
                        </div>
                    </div>
                )}

                <div className="relative flex items-center w-[480px]">
                    {loading ? (
                        <Spinner className="absolute left-3 w-5 h-5 text-[#5D5FEF]" />
                    ) : (
                        <Search className="absolute left-3 w-5 h-5 text-[#5D5FEF]" />
                    )}
                    
                    <Input
                        type="text"
                        placeholder={loading ? "Loading..." : "Search airlines..."}
                        disabled={loading}
                        value={searchInput}
                        onChange={(e) => setSearchInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="w-full h-[45px] bg-[#f5f6fa] pl-10 border-none rounded-2xl text-base"
                    />

                    <Button
                        onClick={handleSearchSubmit}
                        disabled={loading}
                        className="absolute right-0 h-[45px] px-6 border-none rounded-r-2xl rounded-l-none 
                            bg-[#5D5FEF] hover:bg-[#4C4ED0] cursor-pointer text-white text-base font-semibold"
                    >
                        Search
                    </Button>
                </div>

                <span className="text-3xl font-semibold">Dashboard</span>

            </div>
        </div>
    );
};

export default TopBar;
