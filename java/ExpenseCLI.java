import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public class ExpenseCLI {
    static class Expense {
        String date; // YYYY-MM-DD
        String category;
        double amount;
        String description;
    }

    static List<Expense> loadExpenses(File csvFile) throws IOException {
        List<Expense> list = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader(csvFile))) {
            String line;
            boolean headerChecked = false;
            while ((line = br.readLine()) != null) {
                if (line.trim().isEmpty()) continue;
                String[] parts = line.split(",", -1);
                if (!headerChecked) {
                    headerChecked = true;
                    if (parts.length >= 4 && parts[0].trim().equalsIgnoreCase("date") &&
                        parts[1].trim().equalsIgnoreCase("category")) {
                        // header row, skip
                        continue;
                    }
                }
                if (parts.length < 4) continue;
                Expense e = new Expense();
                e.date = parts[0].trim();
                e.category = parts[1].trim();
                try {
                    e.amount = Double.parseDouble(parts[2].trim());
                } catch (NumberFormatException ex) {
                    continue;
                }
                e.description = parts[3].trim();
                list.add(e);
            }
        }
        return list;
    }

    static Map<String, Double> sumByCategory(List<Expense> expenses) {
        Map<String, Double> out = new HashMap<>();
        for (Expense e : expenses) {
            out.put(e.category, out.getOrDefault(e.category, 0.0) + e.amount);
        }
        return out;
    }

    static Map<String, Double> sumByMonth(List<Expense> expenses) {
        Map<String, Double> out = new HashMap<>();
        for (Expense e : expenses) {
            String month = e.date.length() >= 7 ? e.date.substring(0, 7) : e.date; // YYYY-MM
            out.put(month, out.getOrDefault(month, 0.0) + e.amount);
        }
        return out;
    }

    public static void main(String[] args) throws Exception {
        String projectRoot = Paths.get("").toAbsolutePath().toString();
        File csv = Paths.get(projectRoot, "data", "expenses.csv").toFile();
        if (!csv.exists()) {
            System.err.println("expenses.csv not found at: " + csv.getAbsolutePath());
            System.exit(1);
        }
        List<Expense> expenses = loadExpenses(csv);
        System.out.println("Loaded expenses: " + expenses.size());

        Map<String, Double> byCat = sumByCategory(expenses);
        Map<String, Double> byMonth = sumByMonth(expenses);

        System.out.println("\nBy Category:");
        byCat.entrySet().stream()
            .sorted(Map.Entry.comparingByValue(Comparator.reverseOrder()))
            .forEach(e -> System.out.printf(Locale.US, "  %-16s ₹%.2f%n", e.getKey(), e.getValue()));

        System.out.println("\nBy Month:");
        byMonth.entrySet().stream()
            .sorted(Map.Entry.comparingByKey())
            .forEach(e -> System.out.printf(Locale.US, "  %s  ₹%.2f%n", e.getKey(), e.getValue()));
    }
}


