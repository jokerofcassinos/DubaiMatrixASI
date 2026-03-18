package com.dubaimatrix;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadLocalRandom;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * DUBAI MATRIX ASI - JAVA ENTERPRISE PnL v2.0
 * Microservico Distribuido de Predicao de Equity Curve (PhD Optimized)
 */
public class PnLPredictor {

    private static final int PORT = 5556;
    private static final Map<String, String> cache = new ConcurrentHashMap<>();

    public static void main(String[] args) {
        System.out.println("[Java Omega] DubaiMatrixASI PnL Predictor v2.0 Iniciado na porta " + PORT);

        try (ServerSocket serverSocket = new ServerSocket(PORT)) {
            var executor = Executors.newCachedThreadPool(); // Compatibility fallback
            while (true) {
                Socket clientSocket = serverSocket.accept();
                executor.submit(() -> handleClient(clientSocket));
            }
        } catch (Exception e) {
            System.err.println("Falha critica no Kernel Java: " + e.getMessage());
        }
    }

    private static void handleClient(Socket socket) {
        try (
                BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                PrintWriter out = new PrintWriter(socket.getOutputStream(), true)) {
            String inputLine;
            while ((inputLine = in.readLine()) != null) {
                if (inputLine.startsWith("PING")) {
                    out.println("PONG");
                } else if (inputLine.startsWith("UPDATE")) {
                    // UPDATE:balance:win_rate:avg_win:avg_loss:relaxed:risk_frac
                    String[] parts = inputLine.split(":");
                    if (parts.length >= 7) {
                        String cacheKey = inputLine;
                        if (cache.containsKey(cacheKey)) {
                            out.println("ACK:" + cache.get(cacheKey));
                            continue;
                        }

                        double bal = Double.parseDouble(parts[1]);
                        double wr = Double.parseDouble(parts[2]);
                        double aw = Double.parseDouble(parts[3]);
                        double al = Double.parseDouble(parts[4]);
                        boolean relaxed = "true".equalsIgnoreCase(parts[5]);
                        double riskFrac = Double.parseDouble(parts[6]);

                        String prediction = predictPath(bal, wr, aw, al, relaxed, riskFrac);
                        cache.put(cacheKey, prediction);
                        if (cache.size() > 1000) cache.clear(); // Simple LRU-ish
                        
                        out.println("ACK:" + prediction);
                    } else {
                        out.println("ERROR:MALFORMED");
                    }
                } else if (inputLine.equals("QUIT")) {
                    break;
                }
            }
        } catch (Exception e) {
            // Silently close
        }
    }

    private static String predictPath(double equity, double winRate, double avgWin, double avgLoss, boolean relaxedMode, double riskFrac) {
        double successThreshold = relaxedMode ? 0.0005 : 0.01;
        double evFloor = relaxedMode ? -0.1 : 0.0;
        
        if (equity < 5.0) return "IMPOSSIBLE:RUIN";

        double totalProfitNeeded = 1000000.0 - equity;
        if (totalProfitNeeded <= 0) return "GOAL_REACHED:1M_MASTERY";

        int numSimulations = 15000; // Increased precision
        int maxTrades = 500; // Focused horizon
        int successCount = 0;

        double baseRR = Math.abs(avgLoss) > 0.001 ? avgWin / Math.abs(avgLoss) : 1.0;
        double gamma = relaxedMode ? 1.05 : 1.0; // Alpha acceleration in relaxed regimes

        final ThreadLocalRandom random = ThreadLocalRandom.current();

        for (int i = 0; i < numSimulations; i++) {
            double currentEquity = equity;
            for (int t = 0; t < maxTrades; t++) {
                if (currentEquity >= 1000000.0) {
                    successCount++;
                    break;
                }
                if (currentEquity <= 5.0) break;

                // [PHASE Ω-PhD] Non-Linear Drift (Entropy Decay)
                double tFactor = 1.0 - ( (double)t / maxTrades * 0.2 ); // Alpha decays by 20% over 500 trades
                double effectiveWinRate = winRate * tFactor * gamma;
                
                double riskAmount = currentEquity * riskFrac; 
                if (random.nextDouble() < effectiveWinRate) {
                    currentEquity += riskAmount * baseRR;
                } else {
                    currentEquity -= riskAmount;
                }
            }
        }

        double successRate = (double) successCount / numSimulations;
        double ev = (avgWin * winRate * gamma) - (Math.abs(avgLoss) * (1 - winRate * gamma));

        if (successRate < successThreshold && ev <= evFloor) {
           return String.format("IMPOSSIBLE:%s_EXPECTANCY|SR:%.4f|EV:%.4f", 
                   ev <= 0 ? "NEGATIVE" : "LOW", successRate, ev);
        }

        int tradesLeft = (ev > 0) ? (int)(totalProfitNeeded / ev) : 9999;
        return String.format("SUCCESS_PROB:%.4f|TRADES_LEFT:%d|EXPECTED_VALUE:%.4f|MODE:%s", 
                successRate, tradesLeft, ev, relaxedMode ? "RELAXED" : "STRICT");
    }
}

