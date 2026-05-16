import java.awt.BorderLayout;
import java.awt.CardLayout;
import java.awt.GridLayout;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.Socket;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;

public class ChatClient {
    private static final String HOST = "localhost";
    private static final int PORT = 5000;

    private JFrame frame;
    private CardLayout cardLayout;
    private JPanel cards;
    private JTextField usernameField;
    private JPasswordField passwordField;
    private JTextArea chatArea;
    private JTextField messageField;
    private DataInputStream in;
    private DataOutputStream out;
    private boolean connected;

    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                new ChatClient().start();
            }
        });
    }

    private void start() {
        buildGui();
        connect();
    }

    private void buildGui() {
        frame = new JFrame("Chat Client");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(450, 350);

        cardLayout = new CardLayout();
        cards = new JPanel(cardLayout);
        cards.add(createAuthPanel(), "auth");
        cards.add(createChatPanel(), "chat");

        frame.add(cards);
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }

    private JPanel createAuthPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        JPanel fields = new JPanel(new GridLayout(2, 2));
        JPanel buttons = new JPanel();

        usernameField = new JTextField();
        passwordField = new JPasswordField();
        JButton loginButton = new JButton("Login");
        JButton registerButton = new JButton("Register");

        fields.add(new JLabel("Username"));
        fields.add(usernameField);
        fields.add(new JLabel("Password"));
        fields.add(passwordField);

        buttons.add(loginButton);
        buttons.add(registerButton);

        loginButton.addActionListener(e -> sendAuthCommand("/login"));
        registerButton.addActionListener(e -> sendAuthCommand("/register"));

        panel.add(fields, BorderLayout.CENTER);
        panel.add(buttons, BorderLayout.SOUTH);
        return panel;
    }

    private JPanel createChatPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        JPanel bottom = new JPanel(new BorderLayout());
        JButton sendButton = new JButton("Send");

        chatArea = new JTextArea();
        chatArea.setEditable(false);
        messageField = new JTextField();

        bottom.add(messageField, BorderLayout.CENTER);
        bottom.add(sendButton, BorderLayout.EAST);

        sendButton.addActionListener(e -> sendMessage());
        messageField.addActionListener(e -> sendMessage());

        panel.add(new JScrollPane(chatArea), BorderLayout.CENTER);
        panel.add(bottom, BorderLayout.SOUTH);
        return panel;
    }

    private void connect() {
        try {
            Socket socket = new Socket(HOST, PORT);
            in = new DataInputStream(socket.getInputStream());
            out = new DataOutputStream(socket.getOutputStream());
            connected = true;

            Thread reader = new Thread(new Runnable() {
                public void run() {
                    readMessages();
                }
            });
            reader.start();
        } catch (IOException e) {
            JOptionPane.showMessageDialog(frame, "Could not connect to server.");
        }
    }

    private void sendAuthCommand(String command) {
        String username = usernameField.getText().trim();
        String password = new String(passwordField.getPassword()).trim();

        if (username.isEmpty() || password.isEmpty()) {
            JOptionPane.showMessageDialog(frame, "Enter username and password.");
            return;
        }

        send(command + " " + username + " " + password);
    }

    private void sendMessage() {
        String message = messageField.getText().trim();
        if (!message.isEmpty()) {
            send(message);
            messageField.setText("");
        }
    }

    private void send(String message) {
        try {
            if (!connected || out == null) {
                showError("Not connected to server.");
                return;
            }

            out.writeUTF(message);
            out.flush();
        } catch (IOException e) {
            connected = false;
            showError("Could not send message.");
        }
    }

    private void readMessages() {
        try {
            while (true) {
                String message = in.readUTF();
                handleServerMessage(message);
            }
        } catch (IOException e) {
            connected = false;
            showError("Disconnected from server.");
        }
    }

    private void handleServerMessage(String message) {
        if (message.startsWith("LOGIN_OK")) {
            SwingUtilities.invokeLater(new Runnable() {
                public void run() {
                    chatArea.setText("");
                    cardLayout.show(cards, "chat");
                }
            });
        } else if (message.startsWith("REGISTER_OK")) {
            showInfo(message.substring("REGISTER_OK".length()).trim());
        } else if (message.equals("HISTORY_START") || message.equals("HISTORY_END")) {
            return;
        } else if (message.startsWith("MSG ")) {
            appendChat(message.substring(4));
        } else if (message.startsWith("ERROR ")) {
            showError(message.substring(6));
        } else {
            appendChat(message);
        }
    }

    private void appendChat(String message) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                chatArea.append(message + System.lineSeparator());
            }
        });
    }

    private void showInfo(String message) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                JOptionPane.showMessageDialog(frame, message);
            }
        });
    }

    private void showError(String message) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                JOptionPane.showMessageDialog(frame, message);
            }
        });
    }
}
