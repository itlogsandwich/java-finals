import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

public class ChatServer {
    private static final int PORT = 5000;
    private static final String USERS_FILE = "users.txt";
    private static final String HISTORY_FILE = "chat_history.txt";

    private static final CopyOnWriteArrayList<ClientHandler> clients = new CopyOnWriteArrayList<>();
    private static final Map<String, String> users = new ConcurrentHashMap<>();
    private static final Set<String> loggedInUsers = ConcurrentHashMap.newKeySet();
    private static final Object fileLock = new Object();

    public static void main(String[] args) {
        loadUsers();

        try (ServerSocket serverSocket = new ServerSocket(PORT, 50, InetAddress.getLoopbackAddress())) {
            System.out.println("Chat server running on localhost port " + PORT);

            while (true) {
                Socket socket = serverSocket.accept();
                ClientHandler client = new ClientHandler(socket);
                clients.add(client);
                new Thread(client).start();
            }
        } catch (IOException e) {
            System.out.println("Server error: " + e.getMessage());
        }
    }

    private static void loadUsers() {
        File file = new File(USERS_FILE);
        if (!file.exists()) {
            return;
        }

        try (java.util.Scanner scanner = new java.util.Scanner(file)) {
            while (scanner.hasNextLine()) {
                String line = scanner.nextLine();
                String[] parts = line.split(" ", 2);
                if (parts.length == 2) {
                    users.put(parts[0], parts[1]);
                }
            }
        } catch (IOException e) {
            System.out.println("Could not load users: " + e.getMessage());
        }
    }

    private static boolean registerUser(String username, String password) {
        synchronized (fileLock) {
            if (!isValidUsername(username) || password.isEmpty() || users.containsKey(username)) {
                return false;
            }

            users.put(username, password);
            try (FileWriter writer = new FileWriter(USERS_FILE, true)) {
                writer.write(username + " " + password + System.lineSeparator());
                return true;
            } catch (IOException e) {
                users.remove(username);
                return false;
            }
        }
    }

    private static boolean loginUser(String username, String password) {
        if (!isValidUsername(username) || !password.equals(users.get(username))) {
            return false;
        }
        return loggedInUsers.add(username);
    }

    private static boolean isValidUsername(String username) {
        return username.matches("[A-Za-z0-9_]{1,20}");
    }

    private static void sendHistory(ClientHandler client) {
        client.send("HISTORY_START");

        File file = new File(HISTORY_FILE);
        if (file.exists()) {
            try (java.util.Scanner scanner = new java.util.Scanner(file)) {
                while (scanner.hasNextLine()) {
                    client.send("MSG " + scanner.nextLine());
                }
            } catch (IOException e) {
                client.send("SERVER Could not load chat history.");
            }
        }

        client.send("HISTORY_END");
    }

    private static void broadcast(String message) {
        for (ClientHandler client : clients) {
            if (client.isLoggedIn()) {
                client.send("MSG " + message);
            }
        }
    }

    private static void saveMessage(String message) {
        synchronized (fileLock) {
            try (FileWriter writer = new FileWriter(HISTORY_FILE, true)) {
                writer.write(message + System.lineSeparator());
            } catch (IOException e) {
                System.out.println("Could not save message: " + e.getMessage());
            }
        }
    }

    private static String timestamp() {
        return new SimpleDateFormat("HH:mm:ss").format(new Date());
    }

    private static class ClientHandler implements Runnable {
        private final Socket socket;
        private DataInputStream in;
        private DataOutputStream out;
        private String username;

        ClientHandler(Socket socket) {
            this.socket = socket;
        }

        public void run() {
            try {
                in = new DataInputStream(socket.getInputStream());
                out = new DataOutputStream(socket.getOutputStream());

                while (true) {
                    String input = in.readUTF().trim();
                    if (input.startsWith("/register ")) {
                        handleRegister(input);
                    } else if (input.startsWith("/login ")) {
                        handleLogin(input);
                    } else if (isLoggedIn()) {
                        handleMessage(input);
                    } else {
                        send("ERROR Please login first.");
                    }
                }
            } catch (EOFException e) {
                System.out.println("Client disconnected.");
            } catch (IOException e) {
                System.out.println("Client error: " + e.getMessage());
            } finally {
                disconnect();
            }
        }

        private void handleRegister(String input) {
            String[] parts = input.split("\\s+", 3);
            if (parts.length != 3) {
                send("ERROR Usage: /register username password");
                return;
            }

            if (registerUser(parts[1], parts[2])) {
                send("REGISTER_OK Registered successfully.");
            } else {
                send("ERROR Registration failed. Use a unique username with letters, numbers, or underscores.");
            }
        }

        private void handleLogin(String input) {
            if (isLoggedIn()) {
                send("ERROR You are already logged in.");
                return;
            }

            String[] parts = input.split("\\s+", 3);
            if (parts.length != 3) {
                send("ERROR Usage: /login username password");
                return;
            }

            if (loginUser(parts[1], parts[2])) {
                username = parts[1];
                send("LOGIN_OK Logged in.");
                sendHistory(this);
            } else {
                send("ERROR Invalid login or user already logged in.");
            }
        }

        private void handleMessage(String input) {
            if (input.isEmpty()) {
                return;
            }

            String message = "[" + timestamp() + "] " + username + ": " + input;
            saveMessage(message);
            broadcast(message);
        }

        private boolean isLoggedIn() {
            return username != null;
        }

        private void send(String message) {
            try {
                if (out != null) {
                    out.writeUTF(message);
                    out.flush();
                }
            } catch (IOException e) {
                disconnect();
            }
        }

        private void disconnect() {
            clients.remove(this);
            if (username != null) {
                loggedInUsers.remove(username);
                username = null;
            }

            try {
                socket.close();
            } catch (IOException e) {
                System.out.println("Could not close client socket: " + e.getMessage());
            }
        }
    }
}
