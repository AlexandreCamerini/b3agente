-- Tabela do budget guard do gateway (PostgresBudgetStore). Rode uma vez no Neon.
CREATE TABLE IF NOT EXISTS gateway_budget (
    app_id    text PRIMARY KEY,
    day_key   text NOT NULL,
    month_key text NOT NULL,
    day_usd   double precision NOT NULL DEFAULT 0,
    month_usd double precision NOT NULL DEFAULT 0
);
