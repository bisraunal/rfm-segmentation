"""
preprocessing.py
----------------
Adım 1: Veri Temizleme
Adım 2: RFM Metriklerinin Hesaplanması

Desteklenen dosya formatları:
  - online_retail_II.xlsx  (UCI / Kaggle orijinal)
  - raw_data.csv           (alternatif)
  - Herhangi bir .xlsx/.xls veya .csv

Online Retail II kolon yapısı otomatik normalize edilir:
  Invoice      → InvoiceNo
  Price        → UnitPrice
  Customer ID  → CustomerID
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Yollar
# ─────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
DATA_DIR   = BASE_DIR / "data"
CLEAN_FILE = DATA_DIR / "cleaned_data.csv"
RFM_FILE   = DATA_DIR / "rfm_data.csv"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# Online Retail II → standart isim eşlemesi
COLUMN_ALIASES = {
    "Invoice":     "InvoiceNo",
    "Price":       "UnitPrice",
    "Customer ID": "CustomerID",   # boşluklu hâli
}


def _find_raw_file() -> Path:
    """
    data/ klasöründe aşağıdaki öncelik sırasıyla ham veri dosyasını bulur:
      1. online_retail_II.xlsx
      2. raw_data.csv / raw_data.xlsx
      3. Klasördeki ilk .xlsx
      4. Klasördeki ilk .csv
    """
    candidates = [
        DATA_DIR / "online_retail_II.xlsx",
        DATA_DIR / "Online Retail II.xlsx",
        DATA_DIR / "online_retail_ii.xlsx",
        DATA_DIR / "raw_data.csv",
        DATA_DIR / "raw_data.xlsx",
    ]
    for p in candidates:
        if p.exists():
            return p

    # Klasörde herhangi bir xlsx/csv varsa al
    for ext in ("*.xlsx", "*.xls", "*.csv"):
        found = list(DATA_DIR.glob(ext))
        # Temizlenmiş çıktıları atlıyoruz
        found = [f for f in found if "cleaned" not in f.name and "rfm" not in f.name and "cluster" not in f.name]
        if found:
            return found[0]

    return DATA_DIR / "raw_data.csv"   # bulunamazsa örnek veri üretilecek


# ─────────────────────────────────────────────
# ADIM 1 — Veri Yükleme & Temizleme
# ─────────────────────────────────────────────

def load_raw_data(filepath: Path | None = None) -> pd.DataFrame:
    """
    CSV veya XLSX okur; Online Retail II kolon isimlerini normalize eder.
    filepath=None ise data/ klasöründe otomatik arar.
    """
    if filepath is None:
        filepath = _find_raw_file()

    log.info(f"Ham veri yükleniyor: {filepath}")
    suffix = filepath.suffix.lower()

    if suffix in (".xlsx", ".xls"):
        # Online Retail II iki sheet içerebilir (Year 2009-2010 / 2010-2011)
        xl = pd.ExcelFile(filepath, engine="openpyxl")
        sheets = xl.sheet_names
        log.info(f"  Excel sheet'leri: {sheets}")
        frames = [xl.parse(s, dtype=str) for s in sheets]
        df = pd.concat(frames, ignore_index=True)
    else:
        df = pd.read_csv(filepath, encoding="latin-1", dtype=str)

    # Kolon isimlerini normalize et
    df.rename(columns=COLUMN_ALIASES, inplace=True)

    # Sayısal sütunları dönüştür
    for col in ("Quantity", "UnitPrice"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Tarih sütununu dönüştür
    if "InvoiceDate" in df.columns:
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    log.info(f"  → {len(df):,} satır, {df.shape[1]} sütun yüklendi.")
    log.info(f"  Kolonlar: {list(df.columns)}")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Temizleme adımları:
      1. CustomerID eksik olan satırları sil.
      2. Quantity veya UnitPrice <= 0 olan satırları çıkar.
      3. TotalAmount (Quantity × UnitPrice) sütununu ekle.
    """
    log.info("Veri temizleniyor…")
    before = len(df)

    # 1. Eksik CustomerID
    df = df.dropna(subset=["CustomerID"]).copy()
    log.info(f"  Eksik CustomerID silindi   : -{before - len(df):,} satır")

    # 2. Negatif / sıfır Quantity veya UnitPrice
    step = len(df)
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)].copy()
    log.info(f"  Qty/Price ≤ 0 temizlendi   : -{step - len(df):,} satır")

    # 3. TotalAmount
    df["TotalAmount"] = df["Quantity"] * df["UnitPrice"]

    log.info(f"  Kalan satır sayısı         : {len(df):,}")
    return df


def save_clean(df: pd.DataFrame, filepath: Path = CLEAN_FILE) -> None:
    df.to_csv(filepath, index=False)
    log.info(f"Temizlenmiş veri kaydedildi: {filepath}")


# ─────────────────────────────────────────────
# ADIM 2 — RFM Metrikleri
# ─────────────────────────────────────────────

def compute_rfm(df: pd.DataFrame, analysis_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """
    Her CustomerID için:
      - Recency  : Analiz tarihinden son alışverişe kadar geçen gün sayısı
      - Frequency: Benzersiz fatura sayısı
      - Monetary : Toplam harcama
    """
    if analysis_date is None:
        analysis_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    log.info(f"Analiz tarihi: {analysis_date.date()}")

    rfm = (
        df.groupby("CustomerID")
        .agg(
            LastPurchase=("InvoiceDate",  "max"),
            Frequency   =("InvoiceNo",    "nunique"),
            Monetary    =("TotalAmount",  "sum"),
        )
        .reset_index()
    )

    rfm["Recency"] = (analysis_date - rfm["LastPurchase"]).dt.days
    rfm = rfm.drop(columns=["LastPurchase"])
    rfm["Monetary"] = rfm["Monetary"].round(2)

    log.info(f"RFM tablosu oluşturuldu: {len(rfm):,} müşteri")
    return rfm[["CustomerID", "Recency", "Frequency", "Monetary"]]


def save_rfm(rfm: pd.DataFrame, filepath: Path = RFM_FILE) -> None:
    rfm.to_csv(filepath, index=False)
    log.info(f"RFM verisi kaydedildi      : {filepath}")


# ─────────────────────────────────────────────
# Demo / Örnek Veri Üretici
# ─────────────────────────────────────────────

def generate_sample_data(n: int = 5_000, seed: int = 42) -> pd.DataFrame:
    """
    Gerçek veri yoksa test amacıyla rastgele fatura verisi üretir.
    Online Retail II veri setini kullanıyorsanız bu fonksiyona gerek yok.
    """
    rng = np.random.default_rng(seed)
    n_customers = 300

    customer_ids = [f"C{str(i).zfill(4)}" for i in range(1, n_customers + 1)]

    df = pd.DataFrame({
        "InvoiceNo":  [f"INV{i:05d}" for i in range(n)],
        "StockCode":  rng.choice([f"SC{j:03d}" for j in range(50)], size=n),
        "Description": "Sample Product",
        "Quantity":   rng.integers(1, 50, size=n),
        "InvoiceDate": pd.to_datetime("2010-12-01") + pd.to_timedelta(
                            rng.integers(0, 365, size=n), unit="D"),
        "UnitPrice":  np.round(rng.uniform(0.5, 200, size=n), 2),
        "CustomerID": rng.choice(customer_ids, size=n),
        "Country":    "United Kingdom",
    })
    # Biraz hata ekle
    df.loc[rng.choice(n, 100, replace=False), "CustomerID"] = np.nan
    df.loc[rng.choice(n, 50,  replace=False), "Quantity"]   = -1
    return df


# ─────────────────────────────────────────────
# Ana Akış
# ─────────────────────────────────────────────


def run_pipeline(use_sample: bool = False) -> pd.DataFrame:
    found = _find_raw_file()

    if use_sample or not found.exists():
        log.info("Örnek veri üretiliyor (data/ klasöründe dosya bulunamadı)...")
        raw = generate_sample_data()
        raw.to_csv(DATA_DIR / "raw_data.csv", index=False)
        raw = load_raw_data(DATA_DIR / "raw_data.csv")
    else:
        log.info(f"Veri dosyası bulundu: {found.name}")
        raw = load_raw_data(found)

    clean = clean_data(raw)
    save_clean(clean)

    rfm = compute_rfm(clean)
    save_rfm(rfm)
    return rfm


if __name__ == "__main__":
    # data/ klasöründe online_retail_II.xlsx varsa onu kullanır,
    # yoksa örnek veri üretir.
    rfm = run_pipeline()
    print("\n-- RFM Özet İstatistikleri --")
    print(rfm.describe().round(2))