package com.mathblitz.mobile;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.GridLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Space;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final String DEFAULT_BASE_URL = "http://10.0.2.2:8000";

    private static final int BG = Color.rgb(245, 247, 251);
    private static final int SURFACE = Color.WHITE;
    private static final int SURFACE_ALT = Color.rgb(240, 245, 250);
    private static final int INK = Color.rgb(17, 24, 39);
    private static final int TEXT = Color.rgb(31, 41, 55);
    private static final int MUTED = Color.rgb(102, 112, 133);
    private static final int BORDER = Color.rgb(215, 224, 234);
    private static final int BLUE = Color.rgb(0, 114, 178);
    private static final int TEAL = Color.rgb(0, 126, 92);
    private static final int ORANGE = Color.rgb(166, 111, 0);
    private static final int PURPLE = Color.rgb(107, 91, 149);
    private static final int VERMILLION = Color.rgb(213, 94, 0);
    private static final int DANGER = Color.rgb(180, 35, 24);

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private final List<ActivityItem> activities = new ArrayList<>();
    private final List<DifficultyItem> difficulties = new ArrayList<>();
    private final List<JSONObject> leaderboard = new ArrayList<>();

    private SharedPreferences prefs;
    private LinearLayout root;
    private LinearLayout page;
    private TextView status;
    private TextView usernameLabel;
    private TextView scoreLabel;
    private TextView dailyLabel;
    private TextView insightScore;
    private TextView insightDaily;
    private TextView insightAccuracy;
    private TextView insightStreak;
    private TextView taskSkill;
    private TextView taskTitle;
    private TextView taskPrompt;
    private TextView taskHint;
    private TextView taskResult;
    private TextView timerText;
    private EditText answerInput;
    private LinearLayout choiceRow;
    private Button submitButton;
    private Runnable timerTick;

    private String baseUrl;
    private String token;
    private String username;
    private String selectedActivityId = "shopping-value";
    private String selectedDifficulty = "Medium";
    private String currentTaskId;
    private String currentAnswerMode;
    private String selectedChoice;
    private long deadlineMillis;
    private int totalScore;
    private int solvedToday;
    private double accuracy;
    private int streak;
    private int taskGeneration;
    private boolean submitting;
    private String currentView = "auth";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("mathblitz", MODE_PRIVATE);
        baseUrl = prefs.getString("baseUrl", DEFAULT_BASE_URL);
        token = prefs.getString("token", null);
        username = prefs.getString("username", null);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        if (token == null) {
            showAuth();
        } else {
            showApp();
            loadInitialData(true);
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        main.removeCallbacksAndMessages(null);
        executor.shutdownNow();
    }

    private void showAuth() {
        clearTask();
        currentView = "auth";
        main.removeCallbacksAndMessages(null);
        root = baseRoot();
        ScrollView scroll = scroll();
        LinearLayout shell = vertical();
        shell.setPadding(dp(22), dp(24), dp(22), dp(28));
        scroll.addView(shell);
        root.addView(scroll);

        TextView brand = text("MathBlitz", 22, INK, Typeface.BOLD);
        shell.addView(brand);
        shell.addView(kicker("Practical math for everyday decisions", BLUE));
        TextView headline = text("Build sharper judgment with real-life number sense.", 38, INK, Typeface.BOLD);
        headline.setLineSpacing(0, 0.94f);
        shell.addView(headline);
        shell.addView(paragraph("Short scenario challenges for shopping, meetings, home projects, finance, health science, and quick estimates. Designed to be useful from age 5 to 90."));
        shell.addView(metricRow(new String[][]{
                {"12", "daily-life categories"},
                {"5", "difficulty levels"},
                {"120k+", "scenario variations"}
        }));

        LinearLayout panel = card();
        panel.setPadding(dp(22), dp(22), dp(22), dp(22));
        shell.addView(panel, lp(-1, -2, 0, 24, 0, 0));
        panel.addView(kicker("Personal practice workspace", TEAL));
        panel.addView(text("Open MathBlitz", 24, INK, Typeface.BOLD));

        EditText usernameField = input("Username", false);
        EditText passwordField = input("Password", true);
        panel.addView(usernameField, lp(-1, -2, 0, 18, 0, 0));
        panel.addView(passwordField, lp(-1, -2, 0, 12, 0, 0));

        Button signIn = primaryButton("Sign in");
        Button create = secondaryButton("Create account");
        panel.addView(signIn, lp(-1, -2, 0, 18, 0, 0));
        panel.addView(create, lp(-1, -2, 0, 10, 0, 0));
        panel.addView(label("API connection"), lp(-1, -2, 0, 18, 0, 0));
        EditText apiUrl = input("API base URL", false);
        apiUrl.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        apiUrl.setText(baseUrl);
        panel.addView(apiUrl);
        Button saveUrl = ghostButton("Save API URL");
        saveUrl.setOnClickListener(v -> saveBaseUrl(apiUrl));
        panel.addView(saveUrl, lp(-1, -2, 0, 10, 0, 0));
        status = text("", 14, MUTED, Typeface.NORMAL);
        panel.addView(status, lp(-1, -2, 0, 12, 0, 0));

        signIn.setOnClickListener(v -> authenticate("login", usernameField, passwordField));
        create.setOnClickListener(v -> authenticate("register", usernameField, passwordField));
        setContentView(root);
    }

    private void authenticate(String endpoint, EditText usernameField, EditText passwordField) {
        hideKeyboard(passwordField);
        JSONObject body = new JSONObject();
        try {
            body.put("username", usernameField.getText().toString().trim());
            body.put("password", passwordField.getText().toString());
        } catch (Exception ignored) {
        }
        setStatus("Connecting...");
        api("POST", "/api/v1/auth/" + endpoint, body, new JsonCallback() {
            @Override
            public void ok(Object payload) throws Exception {
                JSONObject json = (JSONObject) payload;
                token = json.getString("access_token");
                username = json.getJSONObject("user").getString("username");
                prefs.edit().putString("token", token).putString("username", username).apply();
                showApp();
                loadInitialData(true);
            }

            @Override
            public void fail(String message) {
                setStatus(message);
            }
        });
    }

    private void showApp() {
        scoreLabel = null;
        dailyLabel = null;
        root = baseRoot();
        ScrollView scroll = scroll();
        LinearLayout shell = vertical();
        shell.setPadding(dp(16), dp(18), dp(16), dp(28));
        scroll.addView(shell);
        root.addView(scroll);

        LinearLayout header = card();
        header.setPadding(dp(18), dp(18), dp(18), dp(18));
        shell.addView(header);
        header.addView(kicker("Practical scenario practice", TEAL));
        usernameLabel = text("Hello, " + safe(username), 14, BLUE, Typeface.BOLD);
        header.addView(usernameLabel, lp(-1, -2, 0, 8, 0, 0));
        header.addView(text("Choose a daily-life scenario and make the numbers clear.", 28, INK, Typeface.BOLD));
        header.addView(paragraph("Practice purchases, meetings, housing, commute costs, health science, home projects, and savings decisions."));
        header.addView(metricRow(new String[][]{{"0 / 12", "daily focus"}, {"0", "total score"}}));

        LinearLayout nav = horizontal();
        nav.setGravity(Gravity.CENTER_VERTICAL);
        shell.addView(nav, lp(-1, -2, 0, 14, 0, 16));
        nav.addView(navButton("Practice", () -> renderPractice(true)), weightedLp(1, 0, 0, 0));
        nav.addView(navButton("Library", this::renderLibrary), weightedLp(1, 8, 0, 0));
        nav.addView(navButton("Progress", this::renderProgress), weightedLp(1, 8, 0, 0));
        nav.addView(navButton("Settings", this::renderSettings), weightedLp(1, 8, 0, 0));

        page = vertical();
        shell.addView(page);
        setContentView(root);
    }

    private void loadInitialData(boolean issueTask) {
        setPageLoading("Loading scenario catalog...");
        api("GET", "/api/v1/activities", null, new JsonCallback() {
            @Override
            public void ok(Object payload) throws Exception {
                parseCatalog((JSONObject) payload);
                loadPreferences(issueTask);
            }

            @Override
            public void fail(String message) {
                setPageError(message);
            }
        });
    }

    private void loadPreferences(boolean issueTask) {
        api("GET", "/api/v1/me/preferences", null, new JsonCallback() {
            @Override
            public void ok(Object payload) throws Exception {
                JSONObject json = (JSONObject) payload;
                selectedActivityId = json.optString("default_activity_id", selectedActivityId);
                selectedDifficulty = json.optString("default_difficulty", selectedDifficulty);
                renderPractice(issueTask);
                refreshDashboard();
                refreshLeaderboard();
            }

            @Override
            public void fail(String message) {
                renderPractice(issueTask);
            }
        });
    }

    private void parseCatalog(JSONObject payload) throws Exception {
        activities.clear();
        difficulties.clear();
        JSONArray activityArray = payload.getJSONArray("activities");
        for (int i = 0; i < activityArray.length(); i++) {
            JSONObject item = activityArray.getJSONObject(i);
            activities.add(new ActivityItem(
                    item.getString("id"),
                    item.getString("name"),
                    item.getString("description"),
                    item.getString("skill"),
                    item.optString("accent", "blue"),
                    item.optString("icon", "estimate"),
                    item.optInt("variant_estimate", 10000)
            ));
        }
        JSONArray difficultyArray = payload.getJSONArray("difficulties");
        for (int i = 0; i < difficultyArray.length(); i++) {
            JSONObject item = difficultyArray.getJSONObject(i);
            difficulties.add(new DifficultyItem(
                    item.getString("name"),
                    item.getInt("time_limit_seconds"),
                    item.getInt("points_multiplier")
            ));
        }
        if (findActivity(selectedActivityId) == null && !activities.isEmpty()) {
            selectedActivityId = activities.get(0).id;
        }
    }

    private void renderPractice(boolean issueTask) {
        clearTask();
        currentView = "practice";
        page.removeAllViews();
        page.addView(sectionTitle("Choose a scenario category", "Each category generates thousands of practical, age-flexible challenges."));

        HorizontalScrollView scroller = new HorizontalScrollView(this);
        scroller.setHorizontalScrollBarEnabled(false);
        LinearLayout row = horizontal();
        scroller.addView(row);
        String[] featured = {"shopping-value", "budget-planner", "office-meetings", "health-science"};
        for (String id : featured) {
            ActivityItem item = findActivity(id);
            if (item != null) row.addView(activityCard(item, false), lp(dp(220), dp(116), 0, 0, 0, 12));
        }
        page.addView(scroller);

        page.addView(label("Challenge level"));
        GridLayout difficultyGrid = new GridLayout(this);
        difficultyGrid.setColumnCount(isWide() ? 5 : 2);
        page.addView(difficultyGrid, lp(-1, -2, 0, 8, 0, 14));
        for (DifficultyItem difficulty : difficulties) {
            Button button = cardButton(difficulty.name + "\n" + difficulty.seconds + "s / " + difficulty.multiplier + "x");
            button.setTextColor(difficulty.name.equals(selectedDifficulty) ? Color.WHITE : TEXT);
            button.setBackground(roundRect(difficulty.name.equals(selectedDifficulty) ? BLUE : SURFACE, BORDER, 1, 16));
            button.setOnClickListener(v -> {
                selectedDifficulty = difficulty.name;
                renderPractice(true);
            });
            difficultyGrid.addView(button, gridLp());
        }

        renderTaskCard();
        renderInsightCards();
        if (issueTask) issueTask();
    }

    private void renderTaskCard() {
        LinearLayout task = card();
        task.setPadding(dp(18), dp(18), dp(18), dp(18));
        page.addView(task, lp(-1, -2, 0, 0, 0, 16));

        LinearLayout top = horizontal();
        top.setGravity(Gravity.CENTER_VERTICAL);
        task.addView(top);
        ActivityItem activity = findActivity(selectedActivityId);
        TextView icon = iconBadge(activity == null ? "?" : iconText(activity), accent(activity == null ? "blue" : activity.accent));
        top.addView(icon);
        LinearLayout meta = vertical();
        top.addView(meta, weightedLp(1, 12, 0, 0));
        meta.addView(kicker("Current scenario", BLUE));
        taskSkill = label(activity == null ? "Scenario" : activity.skill);
        taskTitle = text(activity == null ? "Scenario" : activity.name, 20, INK, Typeface.BOLD);
        meta.addView(taskSkill);
        meta.addView(taskTitle);
        timerText = text("-- sec", 18, TEAL, Typeface.BOLD);
        timerText.setGravity(Gravity.CENTER);
        top.addView(timerText);

        taskPrompt = text("Choose a category to begin a practical scenario.", 22, INK, Typeface.BOLD);
        taskPrompt.setBackground(roundRect(SURFACE_ALT, BORDER, 1, 18));
        taskPrompt.setPadding(dp(16), dp(16), dp(16), dp(16));
        task.addView(taskPrompt, lp(-1, -2, 0, 18, 0, 12));

        answerInput = input("Your solution", false);
        answerInput.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL | InputType.TYPE_NUMBER_FLAG_SIGNED);
        task.addView(answerInput);

        choiceRow = horizontal();
        choiceRow.setVisibility(View.GONE);
        Button option1 = secondaryButton("Option 1");
        Button option2 = secondaryButton("Option 2");
        option1.setOnClickListener(v -> chooseOption("1", option1, option2));
        option2.setOnClickListener(v -> chooseOption("2", option2, option1));
        choiceRow.addView(option1, weightedLp(1, 0, 0, 8));
        choiceRow.addView(option2, weightedLp(1, 8, 0, 0));
        task.addView(choiceRow, lp(-1, -2, 0, 12, 0, 0));

        LinearLayout actions = horizontal();
        if (!isWide()) actions.setOrientation(LinearLayout.VERTICAL);
        task.addView(actions, lp(-1, -2, 0, 14, 0, 0));
        submitButton = primaryButton("Submit solution");
        Button hintButton = secondaryButton("Hint");
        Button newButton = ghostButton("New scenario");
        actions.addView(submitButton, isWide() ? weightedLp(1, 0, 0, 8) : lp(-1, -2, 0, 0, 0, 8));
        actions.addView(hintButton, isWide() ? weightedLp(1, 8, 0, 8) : lp(-1, -2, 0, 0, 0, 8));
        actions.addView(newButton, isWide() ? weightedLp(1, 8, 0, 0) : lp(-1, -2));
        submitButton.setOnClickListener(v -> submitAnswer(false));
        hintButton.setOnClickListener(v -> taskHint.setVisibility(taskHint.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE));
        newButton.setOnClickListener(v -> issueTask());

        taskHint = paragraph("Hints guide your approach without revealing the answer.");
        taskHint.setVisibility(View.GONE);
        taskHint.setBackground(roundRect(Color.rgb(231, 242, 250), Color.rgb(197, 223, 240), 1, 16));
        taskHint.setPadding(dp(14), dp(12), dp(14), dp(12));
        task.addView(taskHint, lp(-1, -2, 0, 14, 0, 0));

        taskResult = paragraph("");
        taskResult.setVisibility(View.GONE);
        task.addView(taskResult, lp(-1, -2, 0, 12, 0, 0));
    }

    private void renderInsightCards() {
        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(isWide() ? 4 : 2);
        page.addView(grid);
        LinearLayout daily = metricCard("Daily focus", solvedToday + " / 12");
        LinearLayout score = metricCard("Total score", String.valueOf(totalScore));
        LinearLayout mastery = metricCard("Accuracy", String.format(Locale.US, "%.1f%%", accuracy));
        LinearLayout chain = metricCard("Streak", streak + " solves");
        insightDaily = (TextView) daily.getChildAt(0);
        insightScore = (TextView) score.getChildAt(0);
        insightAccuracy = (TextView) mastery.getChildAt(0);
        insightStreak = (TextView) chain.getChildAt(0);
        grid.addView(daily, gridLp());
        grid.addView(score, gridLp());
        grid.addView(mastery, gridLp());
        grid.addView(chain, gridLp());
    }

    private void clearTask() {
        if (timerTick != null) main.removeCallbacks(timerTick);
        timerTick = null;
        currentTaskId = null;
        submitting = false;
        taskGeneration++;
    }

    private void issueTask() {
        if (activities.isEmpty()) return;
        clearTask();
        final int generation = taskGeneration;
        JSONObject body = new JSONObject();
        try {
            body.put("activity_id", selectedActivityId);
            body.put("difficulty", selectedDifficulty);
        } catch (Exception ignored) {
        }
        submitButton.setEnabled(false);
        taskResult.setVisibility(View.GONE);
        taskPrompt.setText("Loading scenario...");
        api("POST", "/api/v1/tasks", body, new JsonCallback() {
            @Override
            public void ok(Object payload) throws Exception {
                if (generation != taskGeneration || !"practice".equals(currentView)) return;
                JSONObject json = (JSONObject) payload;
                currentTaskId = json.getString("id");
                currentAnswerMode = json.getString("answer_mode");
                selectedChoice = null;
                int seconds = json.getInt("time_limit_seconds");
                deadlineMillis = System.currentTimeMillis() + seconds * 1000L;
                taskTitle.setText(json.getString("activity_name"));
                taskPrompt.setText(json.getString("prompt"));
                taskHint.setText(json.getString("hint"));
                taskHint.setVisibility(View.GONE);
                configureAnswer(currentAnswerMode);
                startTimer();
            }

            @Override
            public void fail(String message) {
                if (generation != taskGeneration || !"practice".equals(currentView)) return;
                showTaskMessage(message, false);
            }
        });
    }

    private void configureAnswer(String mode) {
        boolean choice = "choice".equals(mode);
        answerInput.setText("");
        answerInput.setEnabled(true);
        answerInput.setVisibility(choice ? View.GONE : View.VISIBLE);
        choiceRow.setVisibility(choice ? View.VISIBLE : View.GONE);
        for (int i = 0; i < choiceRow.getChildCount(); i++) {
            choiceRow.getChildAt(i).setEnabled(true);
            choiceRow.getChildAt(i).setBackground(roundRect(SURFACE, BORDER, 1, 14));
        }
        submitButton.setEnabled(!choice);
        if (!choice) answerInput.requestFocus();
    }

    private void chooseOption(String answer, Button selected, Button other) {
        if (currentTaskId == null || submitting) return;
        selectedChoice = answer;
        selected.setBackground(roundRect(Color.rgb(231, 242, 250), BLUE, 2, 14));
        selected.setTextColor(BLUE);
        other.setBackground(roundRect(SURFACE, BORDER, 1, 14));
        other.setTextColor(TEXT);
        submitButton.setEnabled(true);
    }

    private void startTimer() {
        if (timerTick != null) main.removeCallbacks(timerTick);
        timerTick = new Runnable() {
            @Override
            public void run() {
                long remaining = Math.max(0, (deadlineMillis - System.currentTimeMillis() + 999) / 1000);
                timerText.setText(remaining + " sec");
                if (remaining == 0) {
                    submitButton.setEnabled(false);
                    submitAnswer(true);
                    return;
                }
                main.postDelayed(this, 1000);
            }
        };
        main.post(timerTick);
    }

    private void submitAnswer(boolean timeout) {
        if (currentTaskId == null || submitting) return;
        hideKeyboard(answerInput);
        String answer = timeout ? "0" : ("choice".equals(currentAnswerMode) ? selectedChoice : answerInput.getText().toString().trim());
        if (answer == null || answer.isEmpty()) {
            showTaskMessage("Enter a solution first.", false);
            return;
        }
        JSONObject body = new JSONObject();
        try {
            body.put("answer", answer);
        } catch (Exception ignored) {
        }
        submitButton.setEnabled(false);
        submitting = true;
        final int generation = taskGeneration;
        api("POST", "/api/v1/tasks/" + currentTaskId + "/submissions", body, new JsonCallback() {
            @Override
            public void ok(Object payload) throws Exception {
                if (generation != taskGeneration) return;
                clearTask();
                answerInput.setEnabled(false);
                for (int i = 0; i < choiceRow.getChildCount(); i++) choiceRow.getChildAt(i).setEnabled(false);
                JSONObject json = (JSONObject) payload;
                boolean correct = "correct".equals(json.getString("result_status"));
                String message = correct
                        ? "Correct. You earned " + json.getInt("points") + " points."
                        : "Solution: " + json.get("correct_answer");
                showTaskMessage(message, correct);
                refreshDashboard();
                refreshLeaderboard();
            }

            @Override
            public void fail(String message) {
                if (generation != taskGeneration) return;
                submitting = false;
                submitButton.setEnabled(!timeout);
                showTaskMessage(message, false);
            }
        });
    }

    private void showTaskMessage(String message, boolean positive) {
        taskResult.setText(message);
        taskResult.setTextColor(positive ? TEAL : DANGER);
        taskResult.setBackground(roundRect(positive ? Color.rgb(229, 245, 239) : Color.rgb(254, 243, 242), positive ? Color.rgb(191, 227, 214) : Color.rgb(254, 205, 202), 1, 14));
        taskResult.setPadding(dp(12), dp(10), dp(12), dp(10));
        taskResult.setVisibility(View.VISIBLE);
    }

    private void renderLibrary() {
        clearTask();
        currentView = "library";
        page.removeAllViews();
        page.addView(sectionTitle("Scenario library", "Daily-life categories with randomized, choreographed templates."));
        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(isWide() ? 2 : 1);
        page.addView(grid);
        for (ActivityItem item : activities) {
            grid.addView(activityCard(item, true), gridLp());
        }
    }

    private void renderProgress() {
        clearTask();
        currentView = "progress";
        page.removeAllViews();
        page.addView(sectionTitle("Progress", "Your pace, practical accuracy, and leaderboard."));
        GridLayout summary = new GridLayout(this);
        summary.setColumnCount(isWide() ? 4 : 2);
        page.addView(summary);
        summary.addView(metricCard("Solved today", solvedToday + " / 12"), gridLp());
        summary.addView(metricCard("Score", String.valueOf(totalScore)), gridLp());
        summary.addView(metricCard("Accuracy", String.format(Locale.US, "%.1f%%", accuracy)), gridLp());
        summary.addView(metricCard("Streak", streak + " solves"), gridLp());

        page.addView(label("Leaderboard"), lp(-1, -2, 0, 18, 0, 8));
        for (JSONObject entry : leaderboard) {
            try {
                LinearLayout row = card();
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(dp(14), dp(12), dp(14), dp(12));
                row.addView(text("#" + entry.getInt("rank"), 16, BLUE, Typeface.BOLD));
                row.addView(text(entry.getString("username"), 16, INK, Typeface.BOLD), weightedLp(1, 16, 0, 0));
                row.addView(text(entry.getInt("score") + " pts", 14, MUTED, Typeface.BOLD));
                page.addView(row, lp(-1, -2, 0, 0, 0, 8));
            } catch (Exception ignored) {
            }
        }
    }

    private void renderSettings() {
        clearTask();
        currentView = "settings";
        page.removeAllViews();
        page.addView(sectionTitle("Settings", "Connect to a local or hosted MathBlitz API."));
        LinearLayout settings = card();
        settings.setPadding(dp(18), dp(18), dp(18), dp(18));
        page.addView(settings);
        EditText urlInput = input("API base URL", false);
        urlInput.setInputType(InputType.TYPE_TEXT_VARIATION_URI);
        urlInput.setText(baseUrl);
        settings.addView(urlInput);
        Button save = primaryButton("Save API URL");
        settings.addView(save, lp(-1, -2, 0, 14, 0, 0));
        save.setOnClickListener(v -> saveBaseUrl(urlInput));
        Button signOut = ghostButton("Sign out");
        settings.addView(signOut, lp(-1, -2, 0, 10, 0, 0));
        signOut.setOnClickListener(v -> {
            prefs.edit().remove("token").remove("username").apply();
            token = null;
            username = null;
            showAuth();
        });
    }

    private void saveBaseUrl(EditText input) {
        try {
            String value = trimSlash(input.getText().toString().trim());
            URL url = new URL(value);
            if (!("http".equals(url.getProtocol()) || "https".equals(url.getProtocol()))
                    || url.getHost().isEmpty() || url.getUserInfo() != null) {
                throw new IllegalArgumentException("Use an HTTP or HTTPS API URL without credentials.");
            }
            baseUrl = value;
            token = null;
            username = null;
            prefs.edit().putString("baseUrl", baseUrl).remove("token").remove("username").apply();
            showAuth();
            setStatus("API URL saved. Sign in to continue.");
        } catch (Exception error) {
            if ("auth".equals(currentView)) setStatus("Enter a valid HTTP or HTTPS API URL.");
            else setPageError("Enter a valid HTTP or HTTPS API URL.");
        }
    }

    private void refreshDashboard() {
        api("GET", "/api/v1/me/dashboard", null, new JsonCallback() {
            @Override
            public void ok(Object payload) throws Exception {
                JSONObject json = (JSONObject) payload;
                totalScore = json.optInt("score", 0);
                solvedToday = json.optInt("solved_today", 0);
                accuracy = json.optDouble("accuracy", 0);
                streak = json.optInt("streak", 0);
                if (scoreLabel != null) scoreLabel.setText(String.valueOf(totalScore));
                if (dailyLabel != null) dailyLabel.setText(solvedToday + " / 12");
                if ("practice".equals(currentView)) {
                    insightScore.setText(String.valueOf(totalScore));
                    insightDaily.setText(solvedToday + " / 12");
                    insightAccuracy.setText(String.format(Locale.US, "%.1f%%", accuracy));
                    insightStreak.setText(streak + " solves");
                }
            }

            @Override
            public void fail(String message) {
            }
        });
    }

    private void refreshLeaderboard() {
        api("GET", "/api/v1/leaderboard", null, new JsonCallback() {
            @Override
            public void ok(Object payload) throws Exception {
                leaderboard.clear();
                JSONArray array = (JSONArray) payload;
                for (int i = 0; i < array.length(); i++) leaderboard.add(array.getJSONObject(i));
            }

            @Override
            public void fail(String message) {
            }
        });
    }

    private void api(String method, String path, JSONObject body, JsonCallback callback) {
        final String requestBase = baseUrl;
        final String requestToken = token;
        executor.execute(() -> {
            try {
                URL url = new URL(trimSlash(requestBase) + path);
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod(method);
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(12000);
                connection.setRequestProperty("Accept", "application/json");
                connection.setRequestProperty("Content-Type", "application/json");
                if (requestToken != null) connection.setRequestProperty("Authorization", "Bearer " + requestToken);
                if (body != null) {
                    connection.setDoOutput(true);
                    byte[] data = body.toString().getBytes(StandardCharsets.UTF_8);
                    try (OutputStream output = connection.getOutputStream()) {
                        output.write(data);
                    }
                }
                int code = connection.getResponseCode();
                String text = read(code >= 400 ? connection.getErrorStream() : connection.getInputStream());
                Object payload = text.trim().startsWith("[") ? new JSONArray(text) : new JSONObject(text);
                if (!requestBase.equals(baseUrl)) return;
                if (requestToken != null && !requestToken.equals(token)) return;
                if (code == 401 && requestToken != null) {
                    prefs.edit().remove("token").remove("username").apply();
                    main.post(() -> {
                        token = null;
                        username = null;
                        showAuth();
                        setStatus("Your session has ended. Sign in again.");
                    });
                    return;
                }
                if (code >= 400) {
                    String message = payload instanceof JSONObject ? ((JSONObject) payload).optString("detail", "Request failed.") : "Request failed.";
                    main.post(() -> callback.fail(message));
                    return;
                }
                main.post(() -> {
                    try {
                        callback.ok(payload);
                    } catch (Exception error) {
                        callback.fail(error.getMessage());
                    }
                });
            } catch (Exception error) {
                main.post(() -> callback.fail(error.getMessage() == null ? "Connection failed." : error.getMessage()));
            }
        });
    }

    private String read(InputStream stream) throws Exception {
        if (stream == null) return "{}";
        StringBuilder builder = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) builder.append(line);
        }
        return builder.toString();
    }

    private View activityCard(ActivityItem item, boolean large) {
        LinearLayout card = card();
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(14), dp(14), dp(14), dp(14));
        card.setBackground(roundRect(SURFACE, accent(item.accent), 2, 18));
        card.setOnClickListener(v -> {
            selectedActivityId = item.id;
            prefs.edit().putString("activityId", item.id).apply();
            renderPractice(true);
        });
        card.addView(iconBadge(iconText(item), accent(item.accent)));
        LinearLayout copy = vertical();
        card.addView(copy, weightedLp(1, 12, 0, 0));
        copy.addView(text(item.name, 17, INK, Typeface.BOLD));
        copy.addView(text(item.skill.toUpperCase(Locale.US), 12, MUTED, Typeface.BOLD));
        if (large) {
            copy.addView(paragraph(item.description));
            copy.addView(text(Math.round(item.variantEstimate / 1000.0) + "k+ variations", 12, accent(item.accent), Typeface.BOLD));
        }
        card.addView(text(">", 22, accent(item.accent), Typeface.BOLD));
        return card;
    }

    private View sectionTitle(String title, String subtitle) {
        LinearLayout box = vertical();
        box.addView(text(title, 24, INK, Typeface.BOLD));
        box.addView(paragraph(subtitle));
        return box;
    }

    private View metricRow(String[][] metrics) {
        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(isWide() ? metrics.length : 1);
        grid.setPadding(0, dp(18), 0, 0);
        for (String[] metric : metrics) grid.addView(metricCard(metric[1], metric[0]), gridLp());
        return grid;
    }

    private LinearLayout metricCard(String label, String value) {
        LinearLayout card = card();
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        card.addView(text(value, 22, BLUE, Typeface.BOLD));
        card.addView(text(label.toUpperCase(Locale.US), 11, MUTED, Typeface.BOLD));
        if (dailyLabel == null && "daily focus".equalsIgnoreCase(label)) dailyLabel = (TextView) card.getChildAt(0);
        if (scoreLabel == null && "total score".equalsIgnoreCase(label)) scoreLabel = (TextView) card.getChildAt(0);
        return card;
    }

    private Button navButton(String label, Runnable action) {
        Button button = ghostButton(label);
        button.setOnClickListener(v -> action.run());
        return button;
    }

    private LinearLayout baseRoot() {
        LinearLayout view = vertical();
        view.setFitsSystemWindows(true);
        view.setBackgroundColor(BG);
        return view;
    }

    private ScrollView scroll() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        return scroll;
    }

    private LinearLayout card() {
        LinearLayout view = vertical();
        view.setBackground(roundRect(SURFACE, BORDER, 1, 20));
        return view;
    }

    private LinearLayout vertical() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        return layout;
    }

    private LinearLayout horizontal() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.HORIZONTAL);
        return layout;
    }

    private TextView text(String value, int sp, int color, int style) {
        TextView textView = new TextView(this);
        textView.setText(value);
        textView.setTextSize(sp);
        textView.setTextColor(color);
        textView.setTypeface(Typeface.DEFAULT, style);
        textView.setIncludeFontPadding(true);
        return textView;
    }

    private TextView paragraph(String value) {
        TextView textView = text(value, 15, MUTED, Typeface.NORMAL);
        textView.setLineSpacing(dp(2), 1.0f);
        textView.setPadding(0, dp(8), 0, dp(4));
        return textView;
    }

    private TextView kicker(String value, int color) {
        TextView textView = text(value.toUpperCase(Locale.US), 12, color, Typeface.BOLD);
        textView.setLetterSpacing(0.08f);
        textView.setPadding(0, dp(6), 0, dp(8));
        return textView;
    }

    private TextView label(String value) {
        TextView textView = text(value.toUpperCase(Locale.US), 12, MUTED, Typeface.BOLD);
        textView.setPadding(0, dp(8), 0, dp(4));
        return textView;
    }

    private TextView iconBadge(String value, int color) {
        TextView icon = text(value, 17, color, Typeface.BOLD);
        icon.setGravity(Gravity.CENTER);
        icon.setBackground(roundRect(light(color), color, 1, 14));
        icon.setMinWidth(dp(50));
        icon.setMinHeight(dp(50));
        return icon;
    }

    private EditText input(String hint, boolean password) {
        EditText input = new EditText(this);
        input.setHint(hint);
        input.setTextColor(INK);
        input.setHintTextColor(MUTED);
        input.setSingleLine(true);
        input.setPadding(dp(14), 0, dp(14), 0);
        input.setBackground(roundRect(SURFACE, BORDER, 1, 14));
        input.setMinHeight(dp(54));
        input.setInputType(password ? InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD : InputType.TYPE_CLASS_TEXT);
        return input;
    }

    private Button primaryButton(String label) {
        Button button = button(label, Color.WHITE, BLUE);
        return button;
    }

    private Button secondaryButton(String label) {
        Button button = button(label, BLUE, Color.rgb(231, 242, 250));
        button.setBackground(roundRect(Color.rgb(231, 242, 250), Color.rgb(197, 223, 240), 1, 14));
        return button;
    }

    private Button ghostButton(String label) {
        Button button = button(label, TEXT, SURFACE);
        button.setBackground(roundRect(SURFACE, BORDER, 1, 14));
        return button;
    }

    private Button cardButton(String label) {
        Button button = ghostButton(label);
        button.setAllCaps(false);
        button.setMinHeight(dp(74));
        return button;
    }

    private Button button(String label, int textColor, int bgColor) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setTextColor(textColor);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setBackground(roundRect(bgColor, bgColor, 1, 14));
        button.setMinHeight(dp(48));
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        button.setPadding(dp(10), dp(8), dp(10), dp(8));
        return button;
    }

    private GradientDrawable roundRect(int fill, int stroke, int strokeWidth, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fill);
        drawable.setCornerRadius(dp(radius));
        drawable.setStroke(dp(strokeWidth), stroke);
        return drawable;
    }

    private LinearLayout.LayoutParams lp(int width, int height) {
        return new LinearLayout.LayoutParams(width, height);
    }

    private LinearLayout.LayoutParams lp(int width, int height, int left, int top, int right, int bottom) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(width, height);
        params.setMargins(dp(left), dp(top), dp(right), dp(bottom));
        return params;
    }

    private LinearLayout.LayoutParams weightedLp(float weight, int left, int top, int right) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, -2, weight);
        params.setMargins(dp(left), dp(top), dp(right), 0);
        return params;
    }

    private GridLayout.LayoutParams gridLp() {
        GridLayout.LayoutParams params = new GridLayout.LayoutParams();
        params.width = 0;
        params.height = GridLayout.LayoutParams.WRAP_CONTENT;
        params.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
        params.setMargins(dp(4), dp(4), dp(4), dp(8));
        return params;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private boolean isWide() {
        return getResources().getConfiguration().screenWidthDp >= 700
                || getResources().getConfiguration().orientation == Configuration.ORIENTATION_LANDSCAPE;
    }

    private int accent(String name) {
        switch (name) {
            case "teal":
            case "green":
            case "lime":
                return TEAL;
            case "orange":
                return ORANGE;
            case "purple":
            case "violet":
            case "magenta":
            case "pink":
                return PURPLE;
            case "vermillion":
                return VERMILLION;
            default:
                return BLUE;
        }
    }

    private int light(int color) {
        if (color == TEAL) return Color.rgb(229, 245, 239);
        if (color == ORANGE) return Color.rgb(255, 244, 217);
        if (color == PURPLE) return Color.rgb(240, 237, 247);
        if (color == VERMILLION) return Color.rgb(250, 234, 223);
        return Color.rgb(231, 242, 250);
    }

    private String iconText(ActivityItem item) {
        String[] words = item.name.split(" ");
        if (words.length == 1) return words[0].substring(0, Math.min(2, words[0].length())).toUpperCase(Locale.US);
        return (words[0].substring(0, 1) + words[1].substring(0, 1)).toUpperCase(Locale.US);
    }

    private ActivityItem findActivity(String id) {
        for (ActivityItem item : activities) if (item.id.equals(id)) return item;
        return null;
    }

    private String trimSlash(String value) {
        if (value == null || value.isEmpty()) return DEFAULT_BASE_URL;
        while (value.endsWith("/")) value = value.substring(0, value.length() - 1);
        return value;
    }

    private String safe(String value) {
        return value == null ? "friend" : value;
    }

    private void setStatus(String message) {
        if (status != null) status.setText(message);
    }

    private void setPageLoading(String message) {
        if (page == null) return;
        page.removeAllViews();
        page.addView(paragraph(message));
    }

    private void setPageError(String message) {
        if (page == null) return;
        page.removeAllViews();
        TextView error = paragraph(message);
        error.setTextColor(DANGER);
        page.addView(error);
    }

    private void hideKeyboard(View view) {
        try {
            InputMethodManager imm = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
            imm.hideSoftInputFromWindow(view.getWindowToken(), 0);
        } catch (Exception ignored) {
        }
    }

    private interface JsonCallback {
        void ok(Object payload) throws Exception;
        void fail(String message);
    }

    private static class ActivityItem {
        final String id;
        final String name;
        final String description;
        final String skill;
        final String accent;
        final String icon;
        final int variantEstimate;

        ActivityItem(String id, String name, String description, String skill, String accent, String icon, int variantEstimate) {
            this.id = id;
            this.name = name;
            this.description = description;
            this.skill = skill;
            this.accent = accent;
            this.icon = icon;
            this.variantEstimate = variantEstimate;
        }
    }

    private static class DifficultyItem {
        final String name;
        final int seconds;
        final int multiplier;

        DifficultyItem(String name, int seconds, int multiplier) {
            this.name = name;
            this.seconds = seconds;
            this.multiplier = multiplier;
        }
    }
}
