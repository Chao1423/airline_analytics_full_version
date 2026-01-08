import React, { useState, useEffect } from "react";
import useQuery from '../../hooks/useQuery';
import useContext from '../../zustand/useContext';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";

const SubmitContentCard = () => {
    const [searchInput, setSearchInput] = useState("");
    const [submitBody, setSubmitBody] = useState(null);
    const setSentimentData = useContext((state) => state.setSentimentData);
    
    const url = submitBody ? `/sentiment-tool/submit` : null;

    // 对于 POST 请求，每次提交的内容都不同，所以使用较短的缓存时间
    const { data, loading } = useQuery(url, {
        method: 'POST',
        body: submitBody,
        enabled: !!submitBody, // 只在有 body 时启用
        cacheTime: 1 * 60 * 1000, // 缓存 1 分钟（POST 请求通常不需要长时间缓存）
        staleTime: 30 * 1000, // 30 秒内不重新请求
        refetchOnMount: false, // 使用缓存，不重新请求
    });

    useEffect(() => {
        if (data) {
            setSentimentData(data);
            setSubmitBody(null);
        }
    }, [data, setSentimentData]);

    const handleSearchSubmit = () => {
        const trimmedInput = searchInput.trim();
        if (trimmedInput && !loading) {
            setSubmitBody(trimmedInput);
            setSearchInput("");
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !loading) {
            handleSearchSubmit();
        }
    };

    const handleReset = () => {
        setSentimentData("");
        setSearchInput("");
    };
    
    return (
        <Card className="bg-white p-6 rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] flex-1 flex flex-col gap-4 my-2 overflow-hidden">
            <h2 className="text-3xl font-semibold tracking-tight">Submit Content</h2>
            <div className="border-1 border-gray-300 w-full"></div>

            <Textarea
                placeholder={loading ? "Loading..." : "Enter your text here..."}
                disabled={loading}
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 flex max-h-[428px] !text-base"
            />

            <div className="flex gap-2 justify-end">
                <Button
                    onClick={handleReset}
                    disabled={loading}
                    className="h-[45px] px-6 border-none bg-[#5D5FEF] hover:bg-[#4C4ED0] 
                        cursor-pointer text-white text-base font-semibold"
                >
                    Reset
                </Button>

                <Button
                    onClick={handleSearchSubmit}
                    disabled={loading}
                    className="h-[45px] px-6 border-none bg-[#5D5FEF] hover:bg-[#4C4ED0] 
                        cursor-pointer text-white text-base font-semibold"
                >
                    {loading ? <Spinner className="w-5 h-5" /> : "Submit"}
                </Button>
            </div>
        </Card>
    )
}

export default SubmitContentCard