"""
clustering.py
-------------
Adım 3: K-Means ile Kümeleme (ML)
  1. StandardScaler ile ölçeklendirme
  2. Elbow Metodu ile optimum K tespiti
  3. K-Means kümeleme + Cluster ID ekleme
  4. Silhouette skoru hesaplama
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import logging
import warnings

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

BASE_DIR      = Path(__file__).resolve().parent
DATA_DIR      = BASE_DIR / "data"
ASSETS_DIR    = BASE_DIR / "assets"
RFM_FILE      = DATA_DIR / "rfm_data.csv"
CLUSTER_FILE  = DATA_DIR / "rfm_clustered.csv"
ELBOW_IMAGE   = ASSETS_DIR / "elbow_plot.png"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 1. Veri Yükleme & Ölçeklendirme
# ─────────────────────────────────────────────

def load_and_scale(filepath: Path = RFM_FILE):
    """RFM verisini okur, StandardScaler uygular."""
    log.info(f"RFM verisi yükleniyor: {filepath}")
    df = pd.read_csv(filepath)

    features = ["Recency", "Frequency", "Monetary"]

    # Log dönüşümü: outlier etkisini azaltmak için (RFM'de standart pratik)
    X_log = np.log1p(df[features].values)

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X_log)

    log.info(f"  -> {len(df):,} musteri, log dönüsümü + StandardScaler uygulandi.")
    return df, X_scaled, scaler


# ─────────────────────────────────────────────
# 2. Elbow Metodu
# ─────────────────────────────────────────────

def elbow_method(X_scaled: np.ndarray, k_range: range = range(2, 11)) -> dict:
    """
    Farklı K değerleri için inertia ve silhouette skorunu hesaplar.
    Elbow grafiğini çizdirir ve kaydeder.
    """
    log.info("Elbow metodu çalışıyor…")
    inertia     = []
    sil_scores  = []

    for k in k_range:
        km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=42)
        labels = km.fit_predict(X_scaled)
        inertia.append(km.inertia_)
        sil_scores.append(silhouette_score(X_scaled, labels))
        log.info(f"  K={k}  |  Inertia={km.inertia_:,.1f}  |  Silhouette={sil_scores[-1]:.4f}")

    _plot_elbow(list(k_range), inertia, sil_scores)
    return {"k_range": list(k_range), "inertia": inertia, "silhouette": sil_scores}


def _plot_elbow(k_range, inertia, sil_scores):
    """Elbow + Silhouette grafiğini tek figürde çizer."""
    fig = plt.figure(figsize=(13, 5), facecolor="#0f1117")
    gs  = gridspec.GridSpec(1, 2, figure=fig, wspace=0.35)

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    for ax in (ax1, ax2):
        ax.set_facecolor("#1a1d27")
        ax.tick_params(colors="#c9d1d9")
        ax.xaxis.label.set_color("#c9d1d9")
        ax.yaxis.label.set_color("#c9d1d9")
        ax.title.set_color("#e6edf3")
        for spine in ax.spines.values():
            spine.set_edgecolor("#30363d")

    # Elbow
    ax1.plot(k_range, inertia, "o-", color="#58a6ff", linewidth=2.5, markersize=7)
    ax1.fill_between(k_range, inertia, alpha=0.12, color="#58a6ff")
    ax1.set_xlabel("Küme Sayısı (K)", fontsize=12)
    ax1.set_ylabel("Inertia (WCSS)", fontsize=12)
    ax1.set_title("Elbow Metodu", fontsize=14, fontweight="bold")
    ax1.set_xticks(k_range)

    # Silhouette
    colors = ["#3fb950" if s == max(sil_scores) else "#58a6ff" for s in sil_scores]
    bars   = ax2.bar(k_range, sil_scores, color=colors, edgecolor="#30363d", width=0.6)
    ax2.set_xlabel("Küme Sayısı (K)", fontsize=12)
    ax2.set_ylabel("Silhouette Skoru", fontsize=12)
    ax2.set_title("Silhouette Analizi", fontsize=14, fontweight="bold")
    ax2.set_xticks(k_range)
    ax2.set_ylim(0, max(sil_scores) * 1.2)

    # En iyi K vurgula
    best_k = k_range[sil_scores.index(max(sil_scores))]
    ax2.annotate(
        f"En İyi K={best_k}",
        xy=(best_k, max(sil_scores)),
        xytext=(best_k + 0.5, max(sil_scores) * 1.08),
        color="#3fb950",
        fontsize=10,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#3fb950"),
    )

    fig.suptitle("Optimum Küme Sayısı Belirleme", fontsize=16,
                 fontweight="bold", color="#e6edf3", y=1.01)
    plt.savefig(ELBOW_IMAGE, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    log.info(f"Elbow grafiği kaydedildi : {ELBOW_IMAGE}")


def best_k_from_silhouette(elbow_result: dict, min_k: int = 3) -> int:
    """
    En iyi silhouette skoruna sahip K'yı seçer.
    K=2 genellikle sadece outlier'ları ayırdığı için min_k=3'ten başlar.
    """
    k_range    = elbow_result["k_range"]
    sil_scores = elbow_result["silhouette"]

    # min_k'dan büyük olanları filtrele
    valid = [(k, s) for k, s in zip(k_range, sil_scores) if k >= min_k]
    if not valid:
        idx = sil_scores.index(max(sil_scores))
        return k_range[idx]

    best_k, best_score = max(valid, key=lambda x: x[1])
    log.info(f"  Anlamli K aralıginda (>={min_k}) en iyi K = {best_k} (sil={best_score:.4f})")
    return best_k


# ─────────────────────────────────────────────
# 3. K-Means Kümeleme
# ─────────────────────────────────────────────

def apply_kmeans(df: pd.DataFrame, X_scaled: np.ndarray, k: int) -> pd.DataFrame:
    """Seçilen K ile KMeans uygular; Cluster ID ve etiketleri DF'e ekler."""
    log.info(f"K-Means çalıştırılıyor (K={k})…")
    km     = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=42)
    labels = km.fit_predict(X_scaled)

    df = df.copy()
    df["Cluster"] = labels

    # Segmentleri yorumla (Recency düşük = iyi, Monetary yüksek = iyi)
    segment_map = _label_segments(df, k)
    df["Segment"] = df["Cluster"].map(segment_map)

    log.info("Küme dağılımı:")
    for c, seg in sorted(segment_map.items()):
        count = (df["Cluster"] == c).sum()
        log.info(f"  Küme {c} ({seg:<20}) : {count:,} müşteri")

    return df, km


def _label_segments(df: pd.DataFrame, k: int) -> dict:
    """
    Küme ortalamalarına bakarak anlamlı isim atar.
    Recency ↓  Frequency ↑  Monetary ↑  → VIP / Şampiyonlar
    """
    means  = df.groupby("Cluster")[["Recency","Frequency","Monetary"]].mean()
    score  = -means["Recency"] + means["Frequency"] + means["Monetary"].rank()
    ranked = score.rank().astype(int)

    labels = {
        1: "Şampiyonlar",
        2: "Sadık Müşteriler",
        3: "Risk Altındakiler",
        4: "Kaybedilen Müşteriler",
    }
    # K sayısına göre dinamik etiket ata
    segment_labels = ["Kaybedilen Müşteriler", "Risk Altındakiler",
                      "Potansiyel Sadık", "Sadık Müşteriler", "Şampiyonlar"]
    result = {}
    for cluster_id, rank_val in ranked.items():
        idx = min(int(rank_val) - 1, len(segment_labels) - 1)
        result[cluster_id] = segment_labels[idx]
    return result


# ─────────────────────────────────────────────
# 4. Silhouette Skoru
# ─────────────────────────────────────────────

def evaluate_model(X_scaled: np.ndarray, labels: np.ndarray) -> float:
    score = silhouette_score(X_scaled, labels)
    log.info(f"Silhouette Skoru: {score:.4f}  "
             f"({'Mükemmel' if score > 0.5 else 'İyi' if score > 0.3 else 'Orta'})")
    return score


# ─────────────────────────────────────────────
# Ana Akış
# ─────────────────────────────────────────────

def run_clustering(k_override: int | None = None) -> pd.DataFrame:
    df, X_scaled, scaler = load_and_scale()

    elbow  = elbow_method(X_scaled)
    k      = k_override or best_k_from_silhouette(elbow)
    log.info(f"Seçilen K = {k}")

    df_clustered, km = apply_kmeans(df, X_scaled, k)
    sil = evaluate_model(X_scaled, df_clustered["Cluster"].values)

    df_clustered["Silhouette"] = round(sil, 4)
    df_clustered.to_csv(CLUSTER_FILE, index=False)
    log.info(f"Kümelenmiş veri kaydedildi: {CLUSTER_FILE}")

    return df_clustered


if __name__ == "__main__":
    result = run_clustering()
    print("\n── Segment Özeti ──")
    print(
        result.groupby(["Cluster","Segment"])[["Recency","Frequency","Monetary"]]
        .mean()
        .round(1)
        .to_string()
    )