"use client";

import { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { format, parseISO } from "date-fns";

// =============================================================================
// Types
// =============================================================================

interface ChartDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface ChartResponse {
  success: boolean;
  ticker: string;
  period: string;
  data: ChartDataPoint[];
  current_price: number | null;
  price_change: number | null;
  price_change_pct: number | null;
}

interface StockChartProps {
  ticker: string;
  className?: string;
  market?: string;
}

// =============================================================================
// Constants
// =============================================================================

const PERIODS = [
  { key: "1M", label: "1M" },
  { key: "3M", label: "3M" },
  { key: "6M", label: "6M" },
  { key: "1Y", label: "1Y" },
] as const;

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Custom Tooltip
// =============================================================================

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    dataKey: string;
    payload: ChartDataPoint;
  }>;
  label?: string;
  currencySymbol?: string;
}

function CustomTooltip({ active, payload, label, currencySymbol = "₹" }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-background/95 backdrop-blur-sm border border-border rounded-lg p-3 shadow-xl">
      <p className="text-xs text-muted-foreground mb-2">
        {format(parseISO(data.date), "dd MMM yyyy")}
      </p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4 text-sm">
          <span className="text-muted-foreground">Open</span>
          <span className="mono font-medium">{currencySymbol}{data.open.toLocaleString()}</span>
        </div>
        <div className="flex justify-between gap-4 text-sm">
          <span className="text-muted-foreground">High</span>
          <span className="mono font-medium text-emerald-400">{currencySymbol}{data.high.toLocaleString()}</span>
        </div>
        <div className="flex justify-between gap-4 text-sm">
          <span className="text-muted-foreground">Low</span>
          <span className="mono font-medium text-red-400">{currencySymbol}{data.low.toLocaleString()}</span>
        </div>
        <div className="flex justify-between gap-4 text-sm">
          <span className="text-muted-foreground">Close</span>
          <span className="mono font-medium text-primary">{currencySymbol}{data.close.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Stock Chart Component
// =============================================================================

export function StockChart({ ticker, className = "", market = "india" }: StockChartProps) {
  const currencySymbol = market === "us" ? "$" : "₹";
  const [period, setPeriod] = useState<string>("6M");
  const [chartData, setChartData] = useState<ChartResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch chart data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const cleanTicker = ticker.replace(".NS", "");
        const response = await fetch(
          `${API_URL}/chart/${cleanTicker}?period=${period}`
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch chart data`);
        }

        const data: ChartResponse = await response.json();
        setChartData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load chart");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [ticker, period]);

  // Determine chart color based on price change
  const isPositive = chartData?.price_change_pct
    ? chartData.price_change_pct >= 0
    : true;
  const chartColor = isPositive ? "#22c55e" : "#ef4444";
  const gradientId = `gradient-${ticker.replace(/[^a-zA-Z0-9]/g, "")}`;

  // Format Y-axis
  const formatYAxis = (value: number) => {
    if (value >= 1000) {
      return `${currencySymbol}${(value / 1000).toFixed(1)}K`;
    }
    return `${currencySymbol}${value}`;
  };

  // Format X-axis
  const formatXAxis = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), "dd MMM");
    } catch {
      return dateStr;
    }
  };

  return (
    <Card className={`glass-card overflow-hidden ${className}`}>
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h4 className="font-semibold mono">
              {ticker.replace(".NS", "")} Chart
            </h4>
            {chartData && (
              <Badge
                variant="outline"
                className={`gap-1 ${
                  isPositive
                    ? "border-emerald-500/50 text-emerald-400"
                    : "border-red-500/50 text-red-400"
                }`}
              >
                {isPositive ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {chartData.price_change_pct
                  ? `${chartData.price_change_pct >= 0 ? "+" : ""}${chartData.price_change_pct.toFixed(2)}%`
                  : "—"}
              </Badge>
            )}
          </div>

          {/* Period Selector */}
          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <Button
                key={p.key}
                variant={period === p.key ? "default" : "ghost"}
                size="sm"
                onClick={() => setPeriod(p.key)}
                className={`h-7 px-3 text-xs ${
                  period === p.key
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-secondary"
                }`}
              >
                {p.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Chart */}
        <div className="h-[200px] w-full">
          {isLoading ? (
            <div className="h-full w-full flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="h-full w-full flex items-center justify-center">
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          ) : chartData && chartData.data.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={chartData.data}
                margin={{ top: 5, right: 5, left: 0, bottom: 5 }}
              >
                <defs>
                  <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                    <stop
                      offset="0%"
                      stopColor={chartColor}
                      stopOpacity={0.3}
                    />
                    <stop
                      offset="100%"
                      stopColor={chartColor}
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="hsl(var(--border))"
                  strokeOpacity={0.5}
                />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatXAxis}
                  tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                  tickLine={false}
                  axisLine={false}
                  interval="preserveStartEnd"
                  minTickGap={50}
                />
                <YAxis
                  tickFormatter={formatYAxis}
                  tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                  tickLine={false}
                  axisLine={false}
                  domain={["auto", "auto"]}
                  width={55}
                />
                <Tooltip content={<CustomTooltip currencySymbol={currencySymbol} />} />
                <Area
                  type="monotone"
                  dataKey="close"
                  stroke={chartColor}
                  strokeWidth={2}
                  fill={`url(#${gradientId})`}
                  animationDuration={500}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full w-full flex items-center justify-center">
              <p className="text-sm text-muted-foreground">No data available</p>
            </div>
          )}
        </div>

        {/* Stats */}
        {chartData && chartData.data.length > 0 && (
          <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-border/50">
            <div>
              <p className="text-xs text-muted-foreground">Current</p>
              <p className="font-semibold mono">
                {currencySymbol}{chartData.current_price?.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Change</p>
              <p
                className={`font-semibold mono ${
                  isPositive ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {chartData.price_change
                  ? `${chartData.price_change >= 0 ? "+" : ""}${currencySymbol}${Math.abs(chartData.price_change).toLocaleString()}`
                  : "—"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">High ({period})</p>
              <p className="font-semibold mono text-emerald-400">
                {currencySymbol}{Math.max(...chartData.data.map((d) => d.high)).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Low ({period})</p>
              <p className="font-semibold mono text-red-400">
                {currencySymbol}{Math.min(...chartData.data.map((d) => d.low)).toLocaleString()}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

export function StockChartSkeleton() {
  return (
    <Card className="glass-card">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="h-5 w-32" />
          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <Skeleton key={p.key} className="h-7 w-10" />
            ))}
          </div>
        </div>
        <Skeleton className="h-[200px] w-full" />
        <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-border/50">
          {[1, 2, 3, 4].map((i) => (
            <div key={i}>
              <Skeleton className="h-3 w-16 mb-1" />
              <Skeleton className="h-5 w-20" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

