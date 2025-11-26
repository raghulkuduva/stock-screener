"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Play,
  Loader2,
  DollarSign,
  Calendar,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { format, parseISO } from "date-fns";

// =============================================================================
// Types
// =============================================================================

interface Stock {
  ticker: string;
  current_price: number | null;
  [key: string]: unknown;
}

interface StockPerformance {
  ticker: string;
  invested_amount: number;
  shares_bought: number;
  buy_price: number;
  current_price: number;
  current_value: number;
  profit_loss: number;
  return_pct: number;
}

interface SimulationResult {
  success: boolean;
  investment_amount: number;
  period_months: number;
  period_label: string;
  start_date: string;
  end_date: string;
  total_invested: number;
  current_value: number;
  total_profit_loss: number;
  total_return_pct: number;
  stocks: StockPerformance[];
  portfolio_timeline: Array<{ date: string; value: number }>;
}

interface PortfolioSimulatorProps {
  stocks: Stock[];
  market?: string;
}

// =============================================================================
// Constants
// =============================================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PERIODS = [
  { value: "1", label: "1 Month" },
  { value: "2", label: "2 Months" },
  { value: "3", label: "3 Months" },
  { value: "4", label: "4 Months" },
  { value: "5", label: "5 Months" },
  { value: "6", label: "6 Months" },
];

// =============================================================================
// Custom Tooltip
// =============================================================================

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; payload: { date: string; value: number } }>;
  currencySymbol: string;
}

function CustomTooltip({ active, payload, currencySymbol }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-background/95 backdrop-blur-sm border border-border rounded-lg p-3 shadow-xl">
      <p className="text-xs text-muted-foreground mb-1">
        {format(parseISO(data.date), "dd MMM yyyy")}
      </p>
      <p className="font-semibold mono">
        {currencySymbol}
        {data.value.toLocaleString()}
      </p>
    </div>
  );
}

// =============================================================================
// Portfolio Simulator Component
// =============================================================================

export function PortfolioSimulator({ stocks, market = "india" }: PortfolioSimulatorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [amount, setAmount] = useState("");
  const [period, setPeriod] = useState("3");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);

  const currencySymbol = market === "us" ? "$" : "₹";

  const handleSimulate = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      setError("Please enter a valid investment amount");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const tickers = stocks.map((s) => s.ticker);
      
      const response = await fetch(`${API_URL}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tickers,
          investment_amount: parseFloat(amount),
          period_months: parseInt(period),
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Simulation failed");
      }

      const data: SimulationResult = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  const isPositive = result ? result.total_return_pct >= 0 : true;
  const chartColor = isPositive ? "#22c55e" : "#ef4444";

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700">
          <Play className="h-4 w-4" />
          Simulate Performance
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <PieChart className="h-5 w-5 text-emerald-500" />
            Portfolio Performance Simulator
          </DialogTitle>
          <DialogDescription>
            Simulate how your {stocks.length} selected stocks would have performed with equal-weight investment.
          </DialogDescription>
        </DialogHeader>

        {!result ? (
          // Input Form
          <div className="space-y-6 py-4">
            {/* Investment Amount */}
            <div className="space-y-2">
              <Label htmlFor="amount" className="flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                Investment Amount ({currencySymbol})
              </Label>
              <Input
                id="amount"
                type="number"
                placeholder={`e.g., ${market === "us" ? "10000" : "100000"}`}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="mono text-lg"
              />
              <p className="text-xs text-muted-foreground">
                Amount will be equally divided among {stocks.length} stocks ({currencySymbol}
                {amount ? (parseFloat(amount) / stocks.length).toFixed(2) : "0"} per stock)
              </p>
            </div>

            {/* Time Period */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                Simulation Period
              </Label>
              <Select value={period} onValueChange={setPeriod}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PERIODS.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                How far back to simulate the investment (max 6 months)
              </p>
            </div>

            {/* Stocks Preview */}
            <div className="space-y-2">
              <Label>Selected Stocks ({stocks.length})</Label>
              <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto p-2 bg-secondary/30 rounded-lg">
                {stocks.map((s) => (
                  <Badge key={s.ticker} variant="outline" className="mono">
                    {s.ticker.replace(".NS", "")}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive text-sm">
                {error}
              </div>
            )}

            {/* Simulate Button */}
            <Button
              onClick={handleSimulate}
              disabled={isLoading || !amount}
              className="w-full h-12 text-lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Simulating...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-5 w-5" />
                  Run Simulation
                </>
              )}
            </Button>
          </div>
        ) : (
          // Results View
          <div className="space-y-6 py-4">
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="bg-secondary/30">
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">Total Invested</p>
                  <p className="text-xl font-bold mono">
                    {currencySymbol}{result.total_invested.toLocaleString()}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-secondary/30">
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">Current Value</p>
                  <p className={`text-xl font-bold mono ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
                    {currencySymbol}{result.current_value.toLocaleString()}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-secondary/30">
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">Profit/Loss</p>
                  <p className={`text-xl font-bold mono flex items-center gap-1 ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
                    {isPositive ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                    {currencySymbol}{Math.abs(result.total_profit_loss).toLocaleString()}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-secondary/30">
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">Total Return</p>
                  <p className={`text-xl font-bold mono flex items-center gap-1 ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
                    {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                    {result.total_return_pct >= 0 ? "+" : ""}{result.total_return_pct.toFixed(2)}%
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Period Info */}
            <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
              <span>Period: {result.period_label}</span>
              <span>•</span>
              <span>{result.start_date} → {result.end_date}</span>
            </div>

            {/* Portfolio Chart */}
            {result.portfolio_timeline.length > 0 && (
              <Card className="bg-secondary/30">
                <CardContent className="p-4">
                  <h4 className="font-semibold mb-4">Portfolio Value Over Time</h4>
                  <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={result.portfolio_timeline}>
                        <defs>
                          <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={chartColor} stopOpacity={0.3} />
                            <stop offset="100%" stopColor={chartColor} stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} />
                        <XAxis
                          dataKey="date"
                          tickFormatter={(d) => format(parseISO(d), "dd MMM")}
                          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                          tickLine={false}
                          axisLine={false}
                        />
                        <YAxis
                          tickFormatter={(v) => `${currencySymbol}${(v / 1000).toFixed(0)}K`}
                          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                          tickLine={false}
                          axisLine={false}
                          width={60}
                        />
                        <Tooltip content={<CustomTooltip currencySymbol={currencySymbol} />} />
                        <Area
                          type="monotone"
                          dataKey="value"
                          stroke={chartColor}
                          strokeWidth={2}
                          fill="url(#portfolioGradient)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            )}

            <Separator />

            {/* Individual Stock Performance */}
            <div>
              <h4 className="font-semibold mb-4">Individual Stock Performance</h4>
              <div className="max-h-[300px] overflow-y-auto rounded-lg border border-border">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead>Stock</TableHead>
                      <TableHead className="text-right">Invested</TableHead>
                      <TableHead className="text-right">Buy Price</TableHead>
                      <TableHead className="text-right">Current</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                      <TableHead className="text-right">Return</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.stocks
                      .sort((a, b) => b.return_pct - a.return_pct)
                      .map((stock) => (
                        <TableRow key={stock.ticker}>
                          <TableCell className="font-medium mono">{stock.ticker}</TableCell>
                          <TableCell className="text-right mono">
                            {currencySymbol}{stock.invested_amount.toLocaleString()}
                          </TableCell>
                          <TableCell className="text-right mono">
                            {currencySymbol}{stock.buy_price.toLocaleString()}
                          </TableCell>
                          <TableCell className="text-right mono">
                            {currencySymbol}{stock.current_price.toLocaleString()}
                          </TableCell>
                          <TableCell className="text-right mono">
                            {currencySymbol}{stock.current_value.toLocaleString()}
                          </TableCell>
                          <TableCell className={`text-right mono font-medium ${stock.return_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                            {stock.return_pct >= 0 ? "+" : ""}{stock.return_pct.toFixed(2)}%
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </div>
            </div>

            {/* Reset Button */}
            <div className="flex gap-3">
              <Button variant="outline" onClick={handleReset} className="flex-1">
                Simulate Again
              </Button>
              <Button onClick={() => setIsOpen(false)} className="flex-1">
                Close
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

