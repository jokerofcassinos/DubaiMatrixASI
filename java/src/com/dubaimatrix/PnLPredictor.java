package com.dubaimatrix;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicReference;

/**
 * DUBAI MATRIX ASI - JAVA ENTERPRISE PnL
 * Microservico Distribuido de Predicao de Equity Curve
 * 
 * Este daemon roda em background e aceita conexoes socket do Python
 * para computar projecoes complexas de PnL rumo a meta de US$ 1M.
 */
public class PnLPredictor {

    private static final int PORT = 5556;
    private static final AtomicReference<Double> currentBalance = new AtomicReference<>(0.0);
    private static final AtomicReference<Double> winRate = new AtomicReference<>(0.5);

    public static void main(String[] args) {
        System.out.println("[Java Enterprise] DubaiMatrixASI PnL Predictor Iniciado na porta " + PORT);

        try (ServerSocket serverSocket = new ServerSocket(PORT)) {
            var executor = Executors.newCachedThreadPool();
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
                    // UPDATE:balance:win_rate:avg_win:avg_loss
                    String[] parts = inputLine.split(":");
                    if (parts.length == 5) {
                        double bal = Double.parseDouble(parts[1]);
                        double wr = Double.parseDouble(parts[2]);
                        double aw = Double.parseDouble(parts[3]);
                        double al = Double.parseDouble(parts[4]);

                        currentBalance.set(bal);
                        winRate.set(wr);

                        String prediction = predictPath(bal, wr, aw, al);
                        out.println("ACK:" + prediction);
                    } else {
                        out.println("ERROR:MALFORMED");
                    }
                } else if (inputLine.equals("QUIT")) {
                    break;
                }
            }
        } catch (Exception e) {
            System.err.println("Erro na conexao com client: " + e.getMessage());
        }
    }

    private static String predictPath(double equity, double winRate, double avgWin, double avgLoss) {
        // [PHASE OMEGA-FIX] Remove hardcoded bottlenecks. 
        if (equity < 10.0) return "IMPOSSIBLE:INSUFFICIENT_FUNDS";

        double totalProfitNeeded = 1000000.0 - equity;
        if (totalProfitNeeded <= 0) return "GOAL_REACHED:1M_MASTERY";

        // Simulation parameters
        int numSimulations = 10000;
        int maxTrades = 1000;
        int successCount = 0;

        // Dynamic RR calculation
        double rr = Math.abs(avgLoss) > 0.001 ? avgWin / Math.abs(avgLoss) : 1.0;
        
        for (int i = 0; i < numSimulations; i++) {
            double currentEquity = equity;
            for (int t = 0; t < maxTrades; t++) {
                if (currentEquity >= 1000000.0) {
                    successCount++;
                    break;
                }
                if (currentEquity <= 5.0) break; // Ruin threshold

                // Basic compounding sizing (5% risk)
                double riskAmount = currentEquity * 0.05; 
                if (Math.random() < winRate) {
                    currentEquity += riskAmount * rr;
                } else {
                    currentEquity -= riskAmount;
                }
            }
        }

        double successRate = (double) successCount / numSimulations;
        double ev = (avgWin * winRate) - (Math.abs(avgLoss) * (1 - winRate));

        if (successRate < 0.01 && ev <= 0) {
           return "IMPOSSIBLE:NEGATIVE_EXPECTANCY";
        }

        int tradesLeft = (int) (totalProfitNeeded / (ev > 0 ? ev : 0.01));
        return String.format("SUCCESS_PROB:%.2f|TRADES_LEFT:%d|EXPECTED_VALUE:%.2f", successRate, tradesLeft, ev);
    }
}
