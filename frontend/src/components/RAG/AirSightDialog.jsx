import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { MessageSquare, Send, AlertCircle, CheckCircle2 } from "lucide-react";
import axios from "axios";

const makeRequest = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const AirSightDialog = ({ airlineName, startDate, endDate, destination, sentiment }) => {
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleAsk = async () => {
        if (!query.trim() || !airlineName) {
            setError("Please enter a question and select an airline");
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await makeRequest.post('/api/rag/ask', {
                query: query.trim(),
                airline_name: airlineName,
                start_date: startDate || null,
                end_date: endDate || null,
                destination: destination || null,
                sentiment: sentiment || null,
                top_k: 10,
                max_evidence: 5
            });

            if (response.data.status === 'success') {
                setResult(response.data.data);
            } else {
                setError("Failed to get answer");
            }
        } catch (err) {
            setError(err.response?.data?.detail || err.message || "Failed to get answer");
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleAsk();
        }
    };

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] h-full flex flex-col">
            <CardHeader>
                <CardTitle className="text-xl font-semibold flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-[#5D5FEF]" />
                    Ask AirSight (RAG)
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col gap-4 overflow-hidden">
                {/* 输入框 */}
                <div className="flex gap-2">
                    <Input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="e.g., What are the main complaints about this airline in the last 3 months? Give 3 actionable recommendations."
                        className="flex-1"
                        disabled={loading || !airlineName}
                    />
                    <Button
                        onClick={handleAsk}
                        disabled={loading || !airlineName || !query.trim()}
                        className="bg-[#5D5FEF] hover:bg-[#4d4fdf]"
                    >
                        {loading ? (
                            <Spinner className="w-4 h-4" />
                        ) : (
                            <Send className="w-4 h-4" />
                        )}
                    </Button>
                </div>

                {!airlineName && (
                    <div className="text-sm text-gray-500 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        Please select an airline from Dashboard
                    </div>
                )}

                {/* 错误信息 */}
                {error && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <div>{error}</div>
                    </div>
                )}

                {/* 结果 */}
                {result && (
                    <div className="flex-1 overflow-auto space-y-4">
                        {/* 摘要 */}
                        {result.answer?.summary && (
                            <div className="p-4 bg-blue-50 rounded-lg">
                                <div className="font-semibold mb-2 text-blue-900">Summary</div>
                                <div className="text-sm text-blue-800">{result.answer.summary}</div>
                            </div>
                        )}

                        {/* Pain Points */}
                        {result.answer?.pain_points && result.answer.pain_points.length > 0 && (
                            <div>
                                <div className="font-semibold mb-2 text-red-700 flex items-center gap-2">
                                    <AlertCircle className="w-4 h-4" />
                                    Pain Points
                                </div>
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                                    {result.answer.pain_points.map((point, idx) => (
                                        <li key={idx}>{point}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Positive Aspects */}
                        {result.answer?.positive_aspects && result.answer.positive_aspects.length > 0 && (
                            <div>
                                <div className="font-semibold mb-2 text-green-700 flex items-center gap-2">
                                    <CheckCircle2 className="w-4 h-4" />
                                    Positive Aspects
                                </div>
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                                    {result.answer.positive_aspects.map((point, idx) => (
                                        <li key={idx}>{point}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Evidence */}
                        {result.answer?.evidence && result.answer.evidence.length > 0 && (
                            <div>
                                <div className="font-semibold mb-2 text-blue-700 flex items-center gap-2">
                                    <CheckCircle2 className="w-4 h-4" />
                                    Evidence
                                </div>
                                <div className="space-y-2">
                                    {result.answer.evidence.map((ev, idx) => (
                                        <div key={idx} className="p-3 bg-gray-50 rounded border text-sm">
                                            <div className="font-medium text-gray-600 mb-1">
                                                Review ID: {ev.review_id || 'N/A'}
                                            </div>
                                            <div className="text-gray-700 mb-1">{ev.excerpt || ev.point}</div>
                                            {ev.point && (
                                                <div className="text-xs text-gray-500">Supports: {ev.point}</div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        {result.answer?.actions && result.answer.actions.length > 0 && (
                            <div>
                                <div className="font-semibold mb-2 text-green-700 flex items-center gap-2">
                                    <CheckCircle2 className="w-4 h-4" />
                                    Recommended Actions
                                </div>
                                <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                                    {result.answer.actions.map((action, idx) => (
                                        <li key={idx}>{action}</li>
                                    ))}
                                </ol>
                            </div>
                        )}

                        {/* 检索到的评论统计 */}
                        <div className="text-xs text-gray-500 pt-2 border-t">
                            Retrieved {result.retrieved_reviews_count} relevant reviews
                            {result.filters.start_date || result.filters.end_date ? (
                                <span>
                                    {" "}from {result.filters.start_date || 'beginning'} to {result.filters.end_date || 'now'}
                                </span>
                            ) : null}
                        </div>
                    </div>
                )}

                {/* 加载状态 */}
                {loading && (
                    <div className="flex items-center justify-center py-8">
                        <Spinner className="w-8 h-8 text-[#5D5FEF]" />
                        <span className="ml-2 text-sm text-gray-600">Analyzing reviews...</span>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

