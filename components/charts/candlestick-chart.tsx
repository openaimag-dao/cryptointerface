"use client";

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  HistogramSeries,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";

import type { Candle } from "@/types";
import { candleKey, useMarketStore } from "@/store/market-store";

interface CandlestickChartProps {
  data: Candle[];
  height?: number;
  /** When provided (with `interval`), the chart live-updates its last bar
   * from the `/ws/market` feed without a refetch. */
  symbol?: string;
  interval?: string;
}

export function CandlestickChart({ data, height = 420, symbol, interval }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      autoSize: true,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#9aa1a8",
        fontFamily: "var(--font-geist-mono)",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      crosshair: {
        vertLine: { color: "rgba(0,230,118,0.35)", labelBackgroundColor: "#0d0f11" },
        horzLine: { color: "rgba(0,230,118,0.35)", labelBackgroundColor: "#0d0f11" },
      },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
      timeScale: { borderColor: "rgba(255,255,255,0.08)", timeVisible: true, secondsVisible: false },
    });
    chartRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#00e676",
      downColor: "#ff3b5c",
      borderVisible: false,
      wickUpColor: "#00e676",
      wickDownColor: "#ff3b5c",
    });
    candleSeriesRef.current = candleSeries;

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    volumeSeriesRef.current = volumeSeries;
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    candleSeries.setData(
      data.map((candle) => ({
        time: candle.time as UTCTimestamp,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
      })),
    );

    volumeSeries.setData(
      data.map((candle) => ({
        time: candle.time as UTCTimestamp,
        value: candle.volume,
        color: candle.close >= candle.open ? "rgba(0,230,118,0.35)" : "rgba(255,59,92,0.35)",
      })),
    );

    chart.timeScale().fitContent();

    return () => {
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [data, height]);

  useEffect(() => {
    if (!symbol || !interval) return;

    const key = candleKey(symbol, interval);
    const unsubscribe = useMarketStore.subscribe(
      (state) => state.candleUpdates[key],
      (update) => {
        if (!update) return;
        const candleSeries = candleSeriesRef.current;
        const volumeSeries = volumeSeriesRef.current;
        if (!candleSeries || !volumeSeries) return;

        const time = update.candle.time as UTCTimestamp;
        candleSeries.update({
          time,
          open: update.candle.open,
          high: update.candle.high,
          low: update.candle.low,
          close: update.candle.close,
        });
        volumeSeries.update({
          time,
          value: update.candle.volume,
          color: update.candle.close >= update.candle.open ? "rgba(0,230,118,0.35)" : "rgba(255,59,92,0.35)",
        });
      },
    );

    return unsubscribe;
  }, [symbol, interval]);

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
