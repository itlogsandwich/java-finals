import java.awt.BorderLayout;
import java.awt.CardLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.Socket;
import javax.swing.BorderFactory;
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
import javax.swing.UIManager;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;

public class ChatClient {
    private static final String HOST = "localhost";
    private static final int PORT = 5000;

    private static final Color BACKGROUND = new Color(245, 247, 250);
    private static final Color SURFACE = Color.WHITE;
    private static final Color PRIMARY = new Color(37, 99, 235);
    private static final Color PRIMARY_DARK = new Color(29, 78, 216);
    private static final Color ACCENT = new Color(16, 185, 129);
    private static final Color TEXT = new Color(17, 24, 39);
    private static final Color MUTED = new Color(107, 114, 128);
    private static final Color BORDER = new Color(209, 213, 219);
    private static final Color CHAT_BACKGROUND = new Color(249, 250, 251);

    private JFrame frame;
    private CardLayout cardLayout;
    private JPanel cards;
    private JTextField usernameField;
    private JPasswordField passwordField;
    private JTextArea chatArea;
    private JTextField messageField;
    private JLabel authStatusLabel;
    private JLabel chatStatusLabel;
    private JLabel chatTitleLabel;
    private JButton loginButton;
    private JButton registerButton;
    private JButton sendButton;
    private Socket socket;
    private DataInputStream in;
    private DataOutputStream out;
    private boolean connected;
    private String pendingLoginUsername = "";
    private String currentUsername = "";

    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                new ChatClient().start();
            }
        });
    }

    private void start() {
        configureLookAndFeel();
        buildGui();
        connect();
    }

    private void configureLookAndFeel() {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            // Keep Swing's default look and feel if the system theme is unavailable.
        }
    }

    private void buildGui() {
        frame = new JFrame("Java Chat");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setMinimumSize(new Dimension(720, 520));
        frame.setSize(820, 580);
        frame.getContentPane().setBackground(BACKGROUND);

        cardLayout = new CardLayout();
        cards = new JPanel(cardLayout);
        cards.setBackground(BACKGROUND);
        cards.add(createAuthPanel(), "auth");
        cards.add(createChatPanel(), "chat");

        frame.add(cards);
        frame.addWindowListener(new WindowAdapter() {
            public void windowClosing(WindowEvent e) {
                closeConnection();
            }
        });
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }

    private JPanel createAuthPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(BACKGROUND);
        panel.setBorder(new EmptyBorder(32, 32, 32, 32));

        JPanel card = createSurfacePanel();
        card.setPreferredSize(new Dimension(420, 360));
        card.setLayout(new GridBagLayout());

        GridBagConstraints gbc = new GridBagConstraints();
        gbc.gridx = 0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.weightx = 1;

        JLabel title = new JLabel("Java Chat");
        title.setFont(new Font("SansSerif", Font.BOLD, 30));
        title.setForeground(TEXT);
        title.setHorizontalAlignment(JLabel.CENTER);

        JLabel subtitle = new JLabel("Sign in or create an account");
        subtitle.setFont(new Font("SansSerif", Font.PLAIN, 14));
        subtitle.setForeground(MUTED);
        subtitle.setHorizontalAlignment(JLabel.CENTER);

        usernameField = createTextField();
        passwordField = createPasswordField();
        loginButton = createPrimaryButton("Login");
        registerButton = createSecondaryButton("Register");
        authStatusLabel = createStatusLabel("Connecting to server...");

        loginButton.addActionListener(e -> sendAuthCommand("/login"));
        registerButton.addActionListener(e -> sendAuthCommand("/register"));
        passwordField.addActionListener(e -> sendAuthCommand("/login"));

        JPanel buttonRow = new JPanel(new java.awt.GridLayout(1, 2, 10, 0));
        buttonRow.setOpaque(false);
        buttonRow.add(loginButton);
        buttonRow.add(registerButton);

        gbc.gridy = 0;
        gbc.insets = new Insets(0, 0, 4, 0);
        card.add(title, gbc);

        gbc.gridy = 1;
        gbc.insets = new Insets(0, 0, 28, 0);
        card.add(subtitle, gbc);

        gbc.gridy = 2;
        gbc.insets = new Insets(0, 0, 6, 0);
        card.add(createFieldLabel("Username"), gbc);

        gbc.gridy = 3;
        gbc.insets = new Insets(0, 0, 18, 0);
        card.add(usernameField, gbc);

        gbc.gridy = 4;
        gbc.insets = new Insets(0, 0, 6, 0);
        card.add(createFieldLabel("Password"), gbc);

        gbc.gridy = 5;
        gbc.insets = new Insets(0, 0, 24, 0);
        card.add(passwordField, gbc);

        gbc.gridy = 6;
        gbc.insets = new Insets(0, 0, 18, 0);
        card.add(buttonRow, gbc);

        gbc.gridy = 7;
        gbc.insets = new Insets(0, 0, 0, 0);
        card.add(authStatusLabel, gbc);

        panel.add(card);
        return panel;
    }

    private JPanel createChatPanel() {
        JPanel panel = new JPanel(new BorderLayout(0, 0));
        panel.setBackground(BACKGROUND);

        JPanel header = new JPanel(new BorderLayout(12, 0));
        header.setBackground(SURFACE);
        header.setBorder(new CompoundBorder(
                BorderFactory.createMatteBorder(0, 0, 1, 0, BORDER),
                new EmptyBorder(18, 24, 18, 24)));

        chatTitleLabel = new JLabel("Chat room");
        chatTitleLabel.setFont(new Font("SansSerif", Font.BOLD, 22));
        chatTitleLabel.setForeground(TEXT);

        chatStatusLabel = createStatusLabel("Connected");
        chatStatusLabel.setHorizontalAlignment(JLabel.RIGHT);

        header.add(chatTitleLabel, BorderLayout.WEST);
        header.add(chatStatusLabel, BorderLayout.EAST);

        chatArea = new JTextArea();
        chatArea.setEditable(false);
        chatArea.setLineWrap(true);
        chatArea.setWrapStyleWord(true);
        chatArea.setFont(new Font("SansSerif", Font.PLAIN, 14));
        chatArea.setForeground(TEXT);
        chatArea.setBackground(CHAT_BACKGROUND);
        chatArea.setMargin(new Insets(18, 20, 18, 20));

        JScrollPane scrollPane = new JScrollPane(chatArea);
        scrollPane.setBorder(BorderFactory.createEmptyBorder());
        scrollPane.getViewport().setBackground(CHAT_BACKGROUND);

        JPanel composer = new JPanel(new BorderLayout(12, 0));
        composer.setBackground(SURFACE);
        composer.setBorder(new CompoundBorder(
                BorderFactory.createMatteBorder(1, 0, 0, 0, BORDER),
                new EmptyBorder(16, 20, 16, 20)));

        messageField = createTextField();
        messageField.setFont(new Font("SansSerif", Font.PLAIN, 15));
        sendButton = createPrimaryButton("Send");

        composer.add(messageField, BorderLayout.CENTER);
        composer.add(sendButton, BorderLayout.EAST);

        sendButton.addActionListener(e -> sendMessage());
        messageField.addActionListener(e -> sendMessage());

        panel.add(header, BorderLayout.NORTH);
        panel.add(scrollPane, BorderLayout.CENTER);
        panel.add(composer, BorderLayout.SOUTH);
        return panel;
    }

    private JPanel createSurfacePanel() {
        JPanel panel = new JPanel();
        panel.setBackground(SURFACE);
        panel.setBorder(new CompoundBorder(
                new LineBorder(BORDER, 1, true),
                new EmptyBorder(30, 34, 30, 34)));
        return panel;
    }

    private JLabel createFieldLabel(String text) {
        JLabel label = new JLabel(text);
        label.setFont(new Font("SansSerif", Font.BOLD, 13));
        label.setForeground(TEXT);
        return label;
    }

    private JLabel createStatusLabel(String text) {
        JLabel label = new JLabel(text);
        label.setFont(new Font("SansSerif", Font.PLAIN, 13));
        label.setForeground(MUTED);
        return label;
    }

    private JTextField createTextField() {
        JTextField field = new JTextField();
        field.setFont(new Font("SansSerif", Font.PLAIN, 14));
        field.setForeground(TEXT);
        field.setCaretColor(PRIMARY);
        field.setBorder(new CompoundBorder(
                new LineBorder(BORDER, 1, true),
                new EmptyBorder(10, 12, 10, 12)));
        return field;
    }

    private JPasswordField createPasswordField() {
        JPasswordField field = new JPasswordField();
        field.setFont(new Font("SansSerif", Font.PLAIN, 14));
        field.setForeground(TEXT);
        field.setCaretColor(PRIMARY);
        field.setBorder(new CompoundBorder(
                new LineBorder(BORDER, 1, true),
                new EmptyBorder(10, 12, 10, 12)));
        return field;
    }

    private JButton createPrimaryButton(String text) {
        JButton button = new JButton(text);
        styleButton(button, PRIMARY, Color.WHITE);
        return button;
    }

    private JButton createSecondaryButton(String text) {
        JButton button = new JButton(text);
        styleButton(button, new Color(229, 231, 235), TEXT);
        return button;
    }

    private void styleButton(JButton button, Color background, Color foreground) {
        button.setFont(new Font("SansSerif", Font.BOLD, 14));
        button.setBackground(background);
        button.setForeground(foreground);
        button.setFocusPainted(false);
        button.setBorderPainted(false);
        button.setOpaque(true);
        button.setCursor(java.awt.Cursor.getPredefinedCursor(java.awt.Cursor.HAND_CURSOR));
        button.setBorder(new EmptyBorder(10, 18, 10, 18));
    }

    private void connect() {
        setConnectionStatus("Connecting to server...", MUTED);

        try {
            socket = new Socket(HOST, PORT);
            in = new DataInputStream(socket.getInputStream());
            out = new DataOutputStream(socket.getOutputStream());
            connected = true;
            setConnectionStatus("Connected to " + HOST + ":" + PORT, ACCENT);

            Thread reader = new Thread(new Runnable() {
                public void run() {
                    readMessages();
                }
            }, "chat-client-reader");
            reader.setDaemon(true);
            reader.start();
        } catch (IOException e) {
            connected = false;
            setConnectionStatus("Server offline", PRIMARY_DARK);
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

        if ("/login".equals(command)) {
            pendingLoginUsername = username;
        }

        send(command + " " + username + " " + password);
    }

    private void sendMessage() {
        String message = messageField.getText().trim();
        if (!message.isEmpty()) {
            send(message);
            messageField.setText("");
            messageField.requestFocusInWindow();
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
            setConnectionStatus("Disconnected", PRIMARY_DARK);
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
            setConnectionStatus("Disconnected", PRIMARY_DARK);
            showError("Disconnected from server.");
        }
    }

    private void handleServerMessage(String message) {
        if (message.startsWith("LOGIN_OK")) {
            SwingUtilities.invokeLater(new Runnable() {
                public void run() {
                    currentUsername = pendingLoginUsername;
                    chatTitleLabel.setText("Chat room - " + currentUsername);
                    chatArea.setText("");
                    cardLayout.show(cards, "chat");
                    messageField.requestFocusInWindow();
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
                chatArea.setCaretPosition(chatArea.getDocument().getLength());
            }
        });
    }

    private void setConnectionStatus(String message, Color color) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                if (authStatusLabel != null) {
                    authStatusLabel.setText(message);
                    authStatusLabel.setForeground(color);
                }
                if (chatStatusLabel != null) {
                    chatStatusLabel.setText(message);
                    chatStatusLabel.setForeground(color);
                }
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

    private void closeConnection() {
        connected = false;
        try {
            if (socket != null) {
                socket.close();
            }
        } catch (IOException e) {
            // Nothing else to do while the application is closing.
        }
    }
}
