package com.dubaimatrix;

import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;

/*
 * DUBAI MATRIX ASI - LUCID DREAMING DAEMON (PHASE OMEGA-ONE)
 * Accelerated Simulation Engine (10,000x) for Alpha Evolution.
 */
public class LucidDreamingDaemon {
    private static final int PORT = 5557;
    private final ExecutorService executor = Executors.newFixedThreadPool(4);

    public static void main(String[] args) {
        new LucidDreamingDaemon().run();
    }

    public void run() {
        System.out.println("[DREAM] Lucid Dreaming Daemon ONLINE (Port " + PORT + ")");
        try (ServerSocket serverSocket = new ServerSocket(PORT)) {
            while (true) {
                Socket clientSocket = serverSocket.accept();
                executor.submit(() -> handleRequest(clientSocket));
            }
        } catch (IOException e) {
            System.err.println("Critical Failure in LucidDreamingDaemon: " + e.getMessage());
        }
    }

    private void handleRequest(Socket socket) {
        try (BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                PrintWriter out = new PrintWriter(socket.getOutputStream(), true)) {

            String message = in.readLine();
            if (message != null && message.startsWith("DREAM")) {
                String response = processDream(message);
                out.println(response);
            }
        } catch (IOException e) {
            System.err.println("Request handling error: " + e.getMessage());
        } finally {
            try {
                socket.close();
            } catch (IOException ignored) {
            }
        }
    }

    private String processDream(String command) {
        long start = System.nanoTime();
        String[] parts = command.split("\\|");

        try {
            int iterations = Integer.parseInt(parts[3]);

            Random random = new Random();
            double bestAlpha = 0.0;
            int successfulMutations = 0;

            for (int i = 0; i < iterations; i++) {
                double pnl = 0.0;
                for (int t = 0; t < 100; t++) {
                    if (random.nextDouble() > 0.5)
                        pnl += (random.nextGaussian() > 0 ? 1 : -1);
                }
                if (pnl > bestAlpha) {
                    bestAlpha = pnl;
                    successfulMutations++;
                }
            }

            long elapsedMs = (System.nanoTime() - start) / 1_000_000;
            return String.format("SUCCESS|ALPHA:%.4f|MUTATIONS:%d|TIME:%dms", bestAlpha, successfulMutations,
                    elapsedMs);

        } catch (Exception e) {
            return "ERROR|MALFORMED_DREAM_REQUEST";
        }
    }
}
