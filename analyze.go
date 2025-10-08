package main

import (
    "bufio"
    "database/sql"
    "fmt"
    "os"
    "path/filepath"
    "strings"

    _ "github.com/mattn/go-sqlite3"
    "github.com/mitchellh/cli"
)

// AnalyzeCommand extracts embedded SQLite from a binary and summarizes schema/data
type AnalyzeCommand struct {
    ui cli.Ui
}

func (c *AnalyzeCommand) Synopsis() string {
    return "Analyze embedded SQLite DB and summarize schema"
}

func (c *AnalyzeCommand) Help() string {
    return "Usage: clip analyze <binary file(.clip/.cmc)>"
}

func (c *AnalyzeCommand) Run(args []string) int {
    if len(args) != 1 {
        c.ui.Error(c.Help())
        return 1
    }

    in := args[0]
    f, err := os.Open(in)
    if err != nil {
        c.ui.Error(fmt.Sprint(err))
        return 1
    }
    defer f.Close()

    buf := bufio.NewReader(f)
    at, err := seekSQLiteHeader(buf)
    if err != nil {
        c.ui.Error(fmt.Sprint(err))
        return 1
    }

    stat, err := f.Stat()
    if err != nil {
        c.ui.Error(fmt.Sprint(err))
        return 1
    }

    tmp, cleanup, err := makeTempFile()
    if err != nil {
        c.ui.Error(fmt.Sprint(err))
        return 1
    }
    defer cleanup(c.ui)

    if err := extractSQLiteDB(tmp, f, int64(at), stat.Size()); err != nil {
        c.ui.Error(fmt.Sprint(err))
        return 1
    }

    db, err := sql.Open("sqlite3", tmp.Name())
    if err != nil {
        c.ui.Error(fmt.Sprint(err))
        return 1
    }
    defer db.Close()

    // summarize schema
    type tableInfo struct{ name, ttype, sql string }
    rows, err := db.Query("SELECT name, type, COALESCE(sql, '') FROM sqlite_master WHERE type in ('table','view') ORDER BY type, name")
    if err != nil {
        c.ui.Error(fmt.Sprint(err))
        return 1
    }
    defer rows.Close()

    infos := []tableInfo{}
    for rows.Next() {
        var n, t, s string
        if err := rows.Scan(&n, &t, &s); err != nil {
            c.ui.Error(fmt.Sprint(err))
            return 1
        }
        infos = append(infos, tableInfo{n, t, s})
    }

    // build report
    b := &strings.Builder{}
    fmt.Fprintf(b, "Input: %s\n\n", in)
    fmt.Fprintf(b, "Tables/Views (%d)\n", len(infos))
    for _, ti := range infos {
        fmt.Fprintf(b, "- %s (%s)\n", ti.name, ti.ttype)
    }
    fmt.Fprintln(b)

    // sample rows for page-related tables
    for _, ti := range infos {
        if strings.Contains(strings.ToLower(ti.name), "page") || strings.Contains(strings.ToLower(ti.name), "canvas") {
            fmt.Fprintf(b, "# Sample rows from %s\n", ti.name)
            qr := fmt.Sprintf("SELECT * FROM %s LIMIT 5", ti.name)
            r2, err := db.Query(qr)
            if err != nil {
                fmt.Fprintf(b, "(query error: %v)\n\n", err)
                continue
            }
            cols, _ := r2.Columns()
            fmt.Fprintf(b, "cols: %s\n", strings.Join(cols, ", "))
            vals := make([]interface{}, len(cols))
            ptrs := make([]interface{}, len(cols))
            for i := range vals { ptrs[i] = &vals[i] }
            for r2.Next() {
                if err := r2.Scan(ptrs...); err != nil { break }
                parts := make([]string, len(cols))
                for i, v := range vals {
                    if vb, ok := v.([]byte); ok { parts[i] = string(vb) } else if v == nil { parts[i] = "NULL" } else { parts[i] = fmt.Sprint(v) }
                }
                fmt.Fprintf(b, "- %s\n", strings.Join(parts, " | "))
            }
            r2.Close()
            fmt.Fprintln(b)
        }
    }

    // write report under .local
    if !isExists(".local") {
        os.Mkdir(".local", 0755)
    }
    out := filepath.Join(".local", "cmc_analysis.md")
    if err := os.WriteFile(out, []byte(b.String()), 0644); err != nil {
        c.ui.Error(fmt.Sprint(err))
        return 1
    }
    c.ui.Info("Wrote analysis to " + out)
    return 0
}

