"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  Zap,
  Download,
  ChevronDown,
  ChevronUp,
  Info,
  Loader2,
  BarChart3,
  Filter,
  RefreshCcw,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { StockChart } from "@/components/stock-chart";

// =============================================================================
// Types
// =============================================================================

interface Stock {
  ticker: string;
  current_price: number | null;
  ema100: number | null;
  ema200: number | null;
  "52w_high"?: number | null;
  high_52w?: number | null;
  within_25_pct_high: boolean | null;
  up_days_pct_6m: number | null;
  one_year_return_standard: number | null;
  return_6m: number | null;
  return_9m: number | null;
  return_12m: number | null;
  rank_6m: number | null;
  rank_12m: number | null;
  final_rank: number | null;
  gate_pass: boolean | null;
  gate_A_trend: boolean | null;
  gate_B_proximity: boolean | null;
  gate_C_consistency: boolean | null;
  gate_D_performance: boolean | null;
  rejection_reasons: string | null;
}

interface ScreenerResponse {
  success: boolean;
  index_name: string;
  timestamp: string;
  summary: {
    total_analyzed: number;
    passed_filters: number;
    rejected: number;
    pass_rate: number;
  };
  top_stocks: Stock[];
  all_results: Stock[];
  rejected: Stock[];
}

interface Index {
  key: string;
  name: string;
  description: string;
  stock_count: number;
}

// =============================================================================
// Constants
// =============================================================================

const INDICES: (Index & { market: string })[] = [
  // Indian Markets 🇮🇳
  { key: "nifty_50", name: "🇮🇳 Nifty 50", description: "Top 50 Indian companies", stock_count: 50, market: "india" },
  { key: "nifty_next_50", name: "🇮🇳 Nifty Next 50", description: "Next 50 Indian companies", stock_count: 50, market: "india" },
  { key: "nifty_100", name: "🇮🇳 Nifty 100", description: "Top 100 Indian companies", stock_count: 100, market: "india" },
  { key: "nifty_it", name: "🇮🇳 Nifty IT", description: "Indian Tech sector", stock_count: 10, market: "india" },
  { key: "nifty_bank", name: "🇮🇳 Nifty Bank", description: "Indian Banking", stock_count: 12, market: "india" },
  { key: "nifty_pharma", name: "🇮🇳 Nifty Pharma", description: "Indian Pharma", stock_count: 15, market: "india" },
  { key: "nifty_auto", name: "🇮🇳 Nifty Auto", description: "Indian Auto", stock_count: 15, market: "india" },
  { key: "nifty_fmcg", name: "🇮🇳 Nifty FMCG", description: "Indian Consumer", stock_count: 15, market: "india" },
  { key: "nifty_metal", name: "🇮🇳 Nifty Metal", description: "Indian Metal", stock_count: 15, market: "india" },
  { key: "nifty_energy", name: "🇮🇳 Nifty Energy", description: "Indian Energy", stock_count: 10, market: "india" },
  // US Markets 🇺🇸
  { key: "sp500_top50", name: "🇺🇸 S&P 500 Top 50", description: "Top 50 S&P stocks", stock_count: 50, market: "us" },
  { key: "nasdaq_100", name: "🇺🇸 NASDAQ 100", description: "Top NASDAQ stocks", stock_count: 100, market: "us" },
  { key: "dow_jones_30", name: "🇺🇸 Dow Jones 30", description: "30 Dow stocks", stock_count: 30, market: "us" },
  { key: "magnificent_7", name: "🇺🇸 Magnificent 7", description: "Top 7 Tech Giants", stock_count: 7, market: "us" },
  { key: "us_tech", name: "🇺🇸 US Tech", description: "US Tech leaders", stock_count: 30, market: "us" },
  { key: "us_financials", name: "🇺🇸 US Financials", description: "US Banks & Finance", stock_count: 20, market: "us" },
  { key: "us_healthcare", name: "🇺🇸 US Healthcare", description: "US Healthcare", stock_count: 20, market: "us" },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Helper Functions
// =============================================================================

function formatCurrency(value: number | null | undefined, market: string = "india"): string {
  if (value == null) return "—";
  if (market === "us") {
    return `$${value.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  }
  return `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}

function formatPercent(value: number | null | undefined, showSign = true): string {
  if (value == null) return "—";
  const sign = showSign && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function getReturnColor(value: number | null | undefined): string {
  if (value == null) return "text-muted-foreground";
  return value >= 0 ? "text-emerald-400" : "text-red-400";
}

function get52wHigh(stock: Stock): number | null {
  return stock["52w_high"] ?? stock.high_52w ?? null;
}

// =============================================================================
// Components
// =============================================================================

function MetricCard({
  value,
  label,
  icon: Icon,
  color = "text-primary",
}: {
  value: string | number;
  label: string;
  icon: React.ElementType;
  color?: string;
}) {
  return (
    <Card className="glass-card stock-card">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className={`text-3xl font-bold mono ${color}`}>{value}</p>
            <p className="text-sm text-muted-foreground mt-1">{label}</p>
          </div>
          <div className={`p-3 rounded-xl bg-primary/10 ${color}`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function StockCard({ stock, rank, market = "india" }: { stock: Stock; rank: number; market?: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const high52w = get52wHigh(stock);
  const pctFromHigh = high52w && stock.current_price 
    ? ((stock.current_price / high52w) - 1) * 100 
    : null;
  const currencySymbol = market === "us" ? "$" : "₹";

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="glass-card stock-card overflow-hidden">
        <CollapsibleTrigger asChild>
          <CardContent className="p-6 cursor-pointer">
            <div className="flex items-center justify-between">
              {/* Left: Rank & Ticker */}
              <div className="flex items-center gap-4">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-zinc-200 to-zinc-400 text-zinc-900 font-bold mono text-sm">
                  #{rank}
                </div>
                <div>
                  <p className="font-semibold text-lg mono">
                    {stock.ticker.replace(".NS", "")}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {formatCurrency(stock.current_price, market)}
                  </p>
                </div>
              </div>

              {/* Center: Returns */}
              <div className="hidden md:flex items-center gap-8">
                <div className="text-center">
                  <p className={`text-lg font-semibold mono ${getReturnColor(stock.return_6m)}`}>
                    {formatPercent(stock.return_6m)}
                  </p>
                  <p className="text-xs text-muted-foreground">6M Return</p>
                </div>
                <div className="text-center">
                  <p className={`text-lg font-semibold mono ${getReturnColor(stock.return_12m)}`}>
                    {formatPercent(stock.return_12m)}
                  </p>
                  <p className="text-xs text-muted-foreground">12M Return</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold mono text-muted-foreground">
                    {pctFromHigh != null ? `${pctFromHigh.toFixed(1)}%` : "—"}
                  </p>
                  <p className="text-xs text-muted-foreground">From 52W High</p>
                </div>
              </div>

              {/* Right: Expand */}
              <div className="flex items-center gap-3">
                <Badge variant="outline" className="border-primary/50 text-primary">
                  Rank {stock.final_rank?.toFixed(0)}
                </Badge>
                {isOpen ? (
                  <ChevronUp className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
            </div>

            {/* Mobile returns */}
            <div className="flex md:hidden items-center justify-between mt-4 pt-4 border-t border-border/50">
              <div className="text-center">
                <p className={`font-semibold mono ${getReturnColor(stock.return_6m)}`}>
                  {formatPercent(stock.return_6m)}
                </p>
                <p className="text-xs text-muted-foreground">6M</p>
              </div>
              <div className="text-center">
                <p className={`font-semibold mono ${getReturnColor(stock.return_12m)}`}>
                  {formatPercent(stock.return_12m)}
                </p>
                <p className="text-xs text-muted-foreground">12M</p>
              </div>
              <div className="text-center">
                <p className="font-semibold mono text-muted-foreground">
                  {pctFromHigh != null ? `${pctFromHigh.toFixed(1)}%` : "—"}
                </p>
                <p className="text-xs text-muted-foreground">52W</p>
              </div>
            </div>
          </CardContent>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-6 pb-6">
            <Separator className="mb-4" />
            
            {/* Price Chart - Always visible when expanded */}
            <div className="mb-6">
              <StockChart ticker={stock.ticker} market={market} />
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">EMA 100</p>
                <p className="font-semibold mono">{formatCurrency(stock.ema100, market)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">EMA 200</p>
                <p className="font-semibold mono">{formatCurrency(stock.ema200, market)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">52W High</p>
                <p className="font-semibold mono">{formatCurrency(high52w, market)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Up Days %</p>
                <p className="font-semibold mono">{stock.up_days_pct_6m?.toFixed(1)}%</p>
              </div>
            </div>

            {/* Gates */}
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge variant={stock.gate_A_trend ? "default" : "destructive"} className="gap-1">
                {stock.gate_A_trend ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                Trend
              </Badge>
              <Badge variant={stock.gate_B_proximity ? "default" : "destructive"} className="gap-1">
                {stock.gate_B_proximity ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                Strength
              </Badge>
              <Badge variant={stock.gate_C_consistency ? "default" : "destructive"} className="gap-1">
                {stock.gate_C_consistency ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                Consistency
              </Badge>
              <Badge variant={stock.gate_D_performance ? "default" : "destructive"} className="gap-1">
                {stock.gate_D_performance ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                Performance
              </Badge>
            </div>
          </div>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3, 4, 5].map((i) => (
        <Card key={i} className="glass-card">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <Skeleton className="h-10 w-10 rounded-xl" />
              <div className="space-y-2">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-4 w-16" />
              </div>
              <div className="flex-1" />
              <Skeleton className="h-8 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// =============================================================================
// Main Page
// =============================================================================

export default function Home() {
  // State
  const [selectedIndex, setSelectedIndex] = useState<string>("nifty_50");
  const [topN, setTopN] = useState<number>(20);
  const [useStandardReturn, setUseStandardReturn] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [results, setResults] = useState<ScreenerResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Run screener
  const runScreener = async () => {
    setIsLoading(true);
    setProgress(0);
    setError(null);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => Math.min(prev + 5, 90));
    }, 200);

    try {
      const response = await fetch(`${API_URL}/screen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          index_name: selectedIndex,
          top_n: topN,
          use_standard_return: useStandardReturn,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ScreenerResponse = await response.json();
      setResults(data);
      setProgress(100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run screener");
    } finally {
      clearInterval(progressInterval);
      setIsLoading(false);
    }
  };

  // Download CSV
  const downloadCSV = (stocks: Stock[], filename: string) => {
    const headers = [
      "Ticker", "Price", "6M Return", "12M Return", "Final Rank",
      "EMA100", "EMA200", "52W High", "Up Days %",
    ];
    const rows = stocks.map((s) => [
      s.ticker.replace(".NS", ""),
      s.current_price?.toFixed(2) ?? "",
      s.return_6m?.toFixed(2) ?? "",
      s.return_12m?.toFixed(2) ?? "",
      s.final_rank?.toFixed(0) ?? "",
      s.ema100?.toFixed(2) ?? "",
      s.ema200?.toFixed(2) ?? "",
      (s["52w_high"] ?? s.high_52w)?.toFixed(2) ?? "",
      s.up_days_pct_6m?.toFixed(1) ?? "",
    ]);

    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
  };

  const selectedIndexInfo = INDICES.find((i) => i.key === selectedIndex);
  const currentMarket = selectedIndexInfo?.market || "india";

  return (
    <TooltipProvider>
      <div className="min-h-screen radial-gradient-bg noise-overlay">
        {/* Header */}
        <header className="border-b border-border/50 backdrop-blur-sm sticky top-0 z-50 bg-background/80">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-zinc-200 to-zinc-400">
                  <Activity className="h-6 w-6 text-zinc-900" />
                </div>
                <div>
                  <h1 className="text-xl font-bold gradient-text">Momentum Screener</h1>
                  <p className="text-xs text-muted-foreground">Indian Stock Analysis</p>
                </div>
              </div>
              <Badge variant="outline" className="hidden sm:flex gap-1 border-primary/50">
                <Zap className="h-3 w-3 text-primary" />
                Live Data
              </Badge>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8">
          {/* Hero Section */}
          <div className="text-center mb-12 animate-slide-in">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Find <span className="gradient-text">Momentum</span> Stocks
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Screen Indian stocks using technical analysis. Identify high-momentum opportunities
              with our 4-gate filtering system.
            </p>
          </div>

          {/* Controls */}
          <Card className="glass-card mb-8 animate-slide-in-delay-1">
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {/* Index Selection */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Select Index</Label>
                  <Select value={selectedIndex} onValueChange={setSelectedIndex}>
                    <SelectTrigger className="bg-secondary/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {INDICES.map((index) => (
                        <SelectItem key={index.key} value={index.key}>
                          <div className="flex items-center gap-2">
                            <span>{index.name}</span>
                            <span className="text-xs text-muted-foreground">
                              ({index.stock_count})
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {selectedIndexInfo && (
                    <p className="text-xs text-muted-foreground">
                      {selectedIndexInfo.description}
                    </p>
                  )}
                </div>

                {/* Top N Slider */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">
                    Top Stocks: <span className="text-primary mono">{topN}</span>
                  </Label>
                  <Slider
                    value={[topN]}
                    onValueChange={(v) => setTopN(v[0])}
                    min={5}
                    max={50}
                    step={5}
                    className="py-4"
                  />
                </div>

                {/* Standard Return Toggle */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium flex items-center gap-2">
                    Return Formula
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="h-3.5 w-3.5 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="max-w-xs text-xs">
                          Standard formula is recommended for accurate percentage calculations.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </Label>
                  <div className="flex items-center gap-3 pt-2">
                    <Switch
                      checked={useStandardReturn}
                      onCheckedChange={setUseStandardReturn}
                    />
                    <span className="text-sm text-muted-foreground">
                      {useStandardReturn ? "Standard" : "Custom"}
                    </span>
                  </div>
                </div>

                {/* Run Button */}
                <div className="flex items-end">
                  <Button
                    onClick={runScreener}
                    disabled={isLoading}
                    className="w-full h-12 text-lg font-semibold bg-zinc-100 hover:bg-zinc-200 text-zinc-900"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <BarChart3 className="mr-2 h-5 w-5" />
                        Run Screener
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Progress */}
              {isLoading && (
                <div className="mt-6">
                  <Progress value={progress} className="h-2" />
                  <p className="text-xs text-muted-foreground mt-2 text-center">
                    Fetching data and computing indicators...
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Error */}
          {error && (
            <Card className="border-destructive/50 bg-destructive/10 mb-8">
              <CardContent className="p-4 flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-destructive" />
                <div>
                  <p className="font-medium text-destructive">Error running screener</p>
                  <p className="text-sm text-muted-foreground">{error}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={runScreener}
                  className="ml-auto"
                >
                  <RefreshCcw className="h-4 w-4 mr-1" />
                  Retry
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Results */}
          {results && !isLoading && (
            <div className="animate-slide-in">
              {/* Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <MetricCard
                  value={results.summary.total_analyzed}
                  label="Total Analyzed"
                  icon={Filter}
                  color="text-blue-400"
                />
                <MetricCard
                  value={results.summary.passed_filters}
                  label="Passed Filters"
                  icon={CheckCircle2}
                  color="text-emerald-400"
                />
                <MetricCard
                  value={results.summary.rejected}
                  label="Rejected"
                  icon={XCircle}
                  color="text-red-400"
                />
                <MetricCard
                  value={`${results.summary.pass_rate}%`}
                  label="Pass Rate"
                  icon={Target}
                  color="text-primary"
                />
              </div>

              {/* Tabs */}
              <Tabs defaultValue="top" className="space-y-6">
                <TabsList className="grid w-full grid-cols-3 bg-secondary/50">
                  <TabsTrigger value="top" className="gap-2">
                    <TrendingUp className="h-4 w-4" />
                    <span className="hidden sm:inline">Top Momentum</span>
                    <span className="sm:hidden">Top</span>
                  </TabsTrigger>
                  <TabsTrigger value="all" className="gap-2">
                    <BarChart3 className="h-4 w-4" />
                    <span className="hidden sm:inline">All Results</span>
                    <span className="sm:hidden">All</span>
                  </TabsTrigger>
                  <TabsTrigger value="rejected" className="gap-2">
                    <TrendingDown className="h-4 w-4" />
                    Rejected
                  </TabsTrigger>
                </TabsList>

                {/* Top Stocks Tab */}
                <TabsContent value="top" className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold">Top {results.top_stocks.length} Momentum Stocks</h3>
                      <p className="text-sm text-muted-foreground">
                        Ranked by combined 6M and 12M returns
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        downloadCSV(
                          results.top_stocks,
                          `momentum_top_${selectedIndex}_${new Date().toISOString().split("T")[0]}.csv`
                        )
                      }
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Export CSV
                    </Button>
                  </div>

                  {results.top_stocks.length > 0 ? (
                    <div className="space-y-3">
                      {results.top_stocks.map((stock, idx) => (
                        <StockCard key={stock.ticker} stock={stock} rank={idx + 1} market={currentMarket} />
                      ))}
                    </div>
                  ) : (
                    <Card className="glass-card">
                      <CardContent className="p-12 text-center">
                        <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                        <h3 className="text-lg font-semibold mb-2">No Stocks Passed</h3>
                        <p className="text-muted-foreground">
                          No stocks in this index passed all screening criteria.
                        </p>
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                {/* All Results Tab */}
                <TabsContent value="all">
                  <Card className="glass-card overflow-hidden">
                    <CardHeader className="flex flex-row items-center justify-between pb-4">
                      <div>
                        <CardTitle>All Analyzed Stocks</CardTitle>
                        <CardDescription>
                          Complete results with gate status
                        </CardDescription>
        </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          downloadCSV(
                            results.all_results,
                            `momentum_all_${selectedIndex}_${new Date().toISOString().split("T")[0]}.csv`
                          )
                        }
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Export
                      </Button>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow className="border-border/50 hover:bg-transparent">
                              <TableHead className="font-semibold">Ticker</TableHead>
                              <TableHead className="text-right font-semibold">Price</TableHead>
                              <TableHead className="text-right font-semibold">6M</TableHead>
                              <TableHead className="text-right font-semibold">12M</TableHead>
                              <TableHead className="text-center font-semibold">Status</TableHead>
                              <TableHead className="text-center font-semibold">Gates</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {results.all_results.map((stock) => (
                              <TableRow key={stock.ticker} className="border-border/50">
                                <TableCell className="font-medium mono">
                                  {stock.ticker.replace(".NS", "")}
                                </TableCell>
                                <TableCell className="text-right mono">
                                  {formatCurrency(stock.current_price)}
                                </TableCell>
                                <TableCell className={`text-right mono ${getReturnColor(stock.return_6m)}`}>
                                  {formatPercent(stock.return_6m)}
                                </TableCell>
                                <TableCell className={`text-right mono ${getReturnColor(stock.return_12m)}`}>
                                  {formatPercent(stock.return_12m)}
                                </TableCell>
                                <TableCell className="text-center">
                                  {stock.gate_pass ? (
                                    <Badge variant="default" className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                                      Passed
                                    </Badge>
                                  ) : (
                                    <Badge variant="destructive" className="bg-red-500/20 text-red-400 border-red-500/30">
                                      Failed
                                    </Badge>
                                  )}
                                </TableCell>
                                <TableCell>
                                  <div className="flex justify-center gap-1">
                                    {[
                                      { pass: stock.gate_A_trend, label: "T" },
                                      { pass: stock.gate_B_proximity, label: "S" },
                                      { pass: stock.gate_C_consistency, label: "C" },
                                      { pass: stock.gate_D_performance, label: "P" },
                                    ].map((gate, i) => (
                                      <div
                                        key={i}
                                        className={`w-6 h-6 rounded flex items-center justify-center text-xs font-medium ${
                                          gate.pass
                                            ? "bg-emerald-500/20 text-emerald-400"
                                            : "bg-red-500/20 text-red-400"
                                        }`}
                                      >
                                        {gate.label}
                                      </div>
                                    ))}
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Rejected Tab */}
                <TabsContent value="rejected">
                  <Card className="glass-card">
                    <CardHeader>
                      <CardTitle>Rejected Stocks</CardTitle>
                      <CardDescription>
                        Stocks that failed one or more screening criteria
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {results.rejected.length > 0 ? (
                        <div className="space-y-3">
                          {results.rejected.slice(0, 20).map((stock) => (
                            <div
                              key={stock.ticker}
                              className="flex items-center justify-between p-4 rounded-lg bg-secondary/30 border border-border/50"
                            >
                              <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-red-500/10">
                                  <XCircle className="h-4 w-4 text-red-400" />
                                </div>
                                <div>
                                  <p className="font-medium mono">
                                    {stock.ticker.replace(".NS", "")}
                                  </p>
                                  <p className="text-xs text-muted-foreground">
                                    {formatCurrency(stock.current_price)}
                                  </p>
                                </div>
                              </div>
                              <div className="text-right max-w-md">
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                  {stock.rejection_reasons || "Failed screening criteria"}
                                </p>
                              </div>
                            </div>
                          ))}
                          {results.rejected.length > 20 && (
                            <p className="text-center text-sm text-muted-foreground pt-4">
                              +{results.rejected.length - 20} more rejected stocks
                            </p>
                          )}
                        </div>
                      ) : (
                        <p className="text-center text-muted-foreground py-8">
                          All stocks passed the screening criteria!
                        </p>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          )}

          {/* Initial State */}
          {!results && !isLoading && !error && (
            <div className="text-center py-16 animate-slide-in-delay-2">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-zinc-500/20 to-zinc-400/20 mb-6">
                <Target className="h-10 w-10 text-primary" />
              </div>
              <h3 className="text-2xl font-semibold mb-3">Ready to Screen</h3>
              <p className="text-muted-foreground max-w-md mx-auto mb-8">
                Select an index and click Run Screener to identify high-momentum stocks
                using our 4-gate filtering system.
              </p>

              {/* Feature Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
                {[
                  { icon: TrendingUp, label: "Trend Analysis", desc: "EMA crossovers" },
                  { icon: Target, label: "Price Strength", desc: "Near 52W highs" },
                  { icon: Activity, label: "Consistency", desc: "Green day %" },
                  { icon: Zap, label: "Performance", desc: "Yearly returns" },
                ].map((feature, i) => (
                  <Card key={i} className="glass-card p-4">
                    <feature.icon className="h-6 w-6 text-primary mb-2" />
                    <p className="font-medium text-sm">{feature.label}</p>
                    <p className="text-xs text-muted-foreground">{feature.desc}</p>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="border-t border-border/50 mt-16">
          <div className="container mx-auto px-4 py-6">
            <p className="text-center text-sm text-muted-foreground">
              Built with Next.js & shadcn/ui • Data from Yahoo Finance • Not financial advice
            </p>
          </div>
      </footer>
    </div>
    </TooltipProvider>
  );
}
