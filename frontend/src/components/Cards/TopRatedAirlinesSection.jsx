import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import React, { useMemo } from "react";
import { useReactTable, getCoreRowModel, getPaginationRowModel, flexRender } from "@tanstack/react-table";
import useFetch from '../../hooks/useFetch';
import useContext from '../../zustand/useContext';
import { Spinner } from "@/components/ui/spinner";

export const TopRatedAirlinesSection = () => {
    // 使用加权排名，最小评论数50（更合理）
    const { data, loading } = useFetch('/airlines/top-rated?min_reviews=50&use_weighted=true');
    const setTargetAirline = useContext((state) => state.setTargetAirline);

    const columns = [
        {
            accessorKey: "rank",
            header: "#",
            cell: ({ row }) => (
                <div>{row.getValue("rank")}</div>
            ),
        },
        {
            accessorKey: "name",
            header: "Name",
            cell: ({ row }) => (
                <div>{row.getValue("name")}</div>
            ),
        },
        {
            accessorKey: "rating",
            header: "Average Rating",
            cell: ({ row }) => {
                const rating = row.getValue("rating");
                const color = row.original.color;
                return (
                    <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                                className="h-full rounded-full"
                                style={{
                                    width: `${(rating / 10) * 100}%`,
                                    backgroundColor: color,
                                }}
                            />
                        </div>
                    </div>
                );
            },
        },
        {
            accessorKey: "reviewCount",
            header: "Review Count",
            cell: ({ row }) => {
                const count = row.getValue("reviewCount");
                const color = row.original.color;
                return (
                    <div className="text-center">
                        <span
                            className="inline-flex px-3 py-1 rounded-full border-2"
                            style={{ borderColor: color }}
                        >
                            {count}
                        </span>
                    </div>
                );
            },
        },
    ];

    const tableData = useMemo(() => data || [], [data]);

    const table = useReactTable({
        data: tableData,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        initialState: {
            pagination: {
                pageSize: 5,
            },
        },
    });

    return (
        <Card className="bg-white rounded-[20px] border border-[#f8f9fa] shadow-[0px_4px_20px_#ededed80] min-h-[300px]">
            {loading ? (
                <div className="flex items-center justify-center h-full">
                    <Spinner className="w-10 h-10 text-[#5D5FEF]" />
                </div>
            ) : (
                <>
                    <div className="pl-6 text-xl font-semibold">Top Rated Airlines</div>

                    <CardContent>
                        <div className="rounded-md border min-h-[250px] relative">
                            <Table>
                                <TableHeader>
                                    {table.getHeaderGroups().map((headerGroup) => (
                                        <TableRow key={headerGroup.id}>
                                            {headerGroup.headers.map((header) => (
                                                <TableHead
                                                    key={header.id}
                                                    className={`text-gray-500 font-medium text-xs ${
                                                        header.column.id === "reviewCount" ? "text-center" : ""
                                                    }`}
                                                >
                                                    {flexRender(
                                                        header.column.columnDef.header,
                                                        header.getContext()
                                                    )}
                                                </TableHead>
                                            ))}
                                        </TableRow>
                                    ))}
                                </TableHeader>
                                <TableBody>
                                    {table.getRowModel().rows.length ? (
                                        table.getRowModel().rows.map((row) => (
                                            <TableRow 
                                                key={row.id}
                                                className="cursor-pointer hover:bg-gray-50 transition-colors"
                                                onClick={() => {
                                                    const airlineName = row.original.name;
                                                    if (airlineName) {
                                                        setTargetAirline(airlineName);
                                                    }
                                                }}
                                            >
                                                {row.getVisibleCells().map((cell) => (
                                                    <TableCell key={cell.id} className="font-medium text-xs">
                                                        {flexRender(
                                                            cell.column.columnDef.cell,
                                                            cell.getContext()
                                                        )}
                                                    </TableCell>
                                                ))}
                                            </TableRow>
                                        ))
                                    ) : (
                                        <TableRow>
                                            <TableCell colSpan={table.getAllColumns().length} className="p-0 h-0 border-none" />
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>

                            {!table.getRowModel().rows.length && (
                                <div className="absolute top-[40px] bottom-0 left-0 right-0 flex items-center justify-center">
                                    <span className="text-xl font-semibold text-center">📊 No airline data available</span>
                                </div>
                            )}
                        </div>

                        <div className="flex items-center justify-end gap-2 pt-4">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => table.previousPage()}
                                disabled={!table.getCanPreviousPage()}
                            >
                                Previous
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => table.nextPage()}
                                disabled={!table.getCanNextPage()}
                            >
                                Next
                            </Button>
                        </div>
                    </CardContent>
                </>
            )}
        </Card>
    );
};

export default TopRatedAirlinesSection;