import io
import time
import pandas as pd
import streamlit as st

import rsa_benchmark as rsa
import test_rsa_benchmark as test_runner

st.set_page_config(
    page_title="RSA & RSA-CRT Benchmark Lab",
    page_icon="[RSA]",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #1E88E5;
        margin-bottom: 10px;
    }
    .stMetric {
        background: rgba(240, 242, 246, 0.5);
        padding: 12px;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.title("RSA vs RSA-CRT")
    st.markdown("**Laboratorium Kriptografi & Komparasi Waktu Dekripsi**")
    st.markdown("---")
    st.markdown(
        """
        ### Mengapa RSA-CRT?
        Pada RSA standar, dekripsi menghitung:
        $$M = C^d \\pmod n$$
        dengan $n$ yang sangat besar ($p \\times q$).
        
        Dengan **Chinese Remainder Theorem (CRT)**:
        - Eksponen dipotong menjadi $d_P$ dan $d_Q$ (sekitar separuh panjang bit $d$).
        - Modulus dipotong menjadi $p$ dan $q$ (separuh bit $n$).
        - Karena kompleksitas perkalian modular berkurang drastis, dekripsi CRT umumnya **~3x hingga 4x lebih cepat**.
        """
    )
    st.markdown("---")
    st.caption("Proyek Matematika Diskrit • Pure Python 3 & Streamlit")

# Main Page Header
st.title("Dashboard Interaktif RSA & RSA-CRT")
st.markdown(
    "Aplikasi web untuk simulasi langkah matematis, pengujian performa eksekusi, "
    "dan verifikasi kasus uji algoritma RSA vs RSA-CRT."
)

tab_calc, tab_bench, tab_test = st.tabs([
    "1. Simulasi & Langkah Matematis",
    "2. Benchmark & Visualisasi Grafik",
    "3. Verifikasi Kasus Uji (Test Suite)"
])

# ==========================================================
# TAB 1: KALKULATOR & LANGKAH MATEMATIS
# ==========================================================
with tab_calc:
    st.header("Simulasi Kunci, Enkripsi & Dekripsi Langkah-demi-Langkah")
    st.write(
        "Masukkan parameter manual atau gunakan preset bawaan untuk melihat detail "
        "rumus dan perhitungan modular RSA vs RSA-CRT."
    )

    preset_choice = st.selectbox(
        "Pilih Preset Data Uji:",
        [
            "Preset 1: Kasus Contoh Laporan (p=43, q=59, e=13, M=1819)",
            "Preset 2: Kasus Valid V2 (p=61, q=53, e=17, M=65)",
            "Preset 3: Kasus Valid V5 (p=17, q=61, e=7, M=42)",
            "Input Manual (Kustom)",
        ],
    )

    if preset_choice.startswith("Preset 1"):
        default_p, default_q, default_e, default_m = 43, 59, 13, 1819
    elif preset_choice.startswith("Preset 2"):
        default_p, default_q, default_e, default_m = 61, 53, 17, 65
    elif preset_choice.startswith("Preset 3"):
        default_p, default_q, default_e, default_m = 17, 61, 7, 42
    else:
        default_p, default_q, default_e, default_m = 43, 59, 13, 1819

    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    with col_in1:
        p_val = st.text_input("Prima p:", value=str(default_p))
    with col_in2:
        q_val = st.text_input("Prima q:", value=str(default_q))
    with col_in3:
        e_val = st.text_input("Eksponen Publik e:", value=str(default_e))
    with col_in4:
        m_val = st.text_input("Pesan M (0 <= M < n):", value=str(default_m))

    mr_check_rounds = st.slider("Jumlah Ronde Miller-Rabin untuk Validasi Prima:", 1, 50, 20)

    if st.button("Hitung & Jalankan Simulasi", type="primary", use_container_width=True):
        try:
            p_val, q_val, e_val, m_val = map(int, (p_val, q_val, e_val, m_val))
            # 1. Validasi Miller-Rabin
            if not rsa.prima_miller_rabin(p_val, mr_check_rounds):
                st.error(f"[GAGAL] Parameter p = {p_val} tidak lolos pengujian prima Miller-Rabin.")
                st.stop()
            if not rsa.prima_miller_rabin(q_val, mr_check_rounds):
                st.error(f"[GAGAL] Parameter q = {q_val} tidak lolos pengujian prima Miller-Rabin.")
                st.stop()

            # 2. Bangkitkan Kunci
            kunci = rsa.bangkitkan_kunci(p_val, q_val, e_val)
            
            # 3. Validasi Pesan
            if not (0 <= m_val < kunci["n"]):
                st.error(f"[GAGAL] Pesan M harus memenuhi 0 <= M < n (0 <= {m_val} < {kunci['n']}).")
                st.stop()

            # 4. Enkripsi & Dekripsi
            c = rsa.enkripsi(m_val, kunci["e"], kunci["n"])
            m_rsa = rsa.dekripsi_rsa(c, kunci["d"], kunci["n"])
            m_crt = rsa.dekripsi_crt(c, p_val, q_val, kunci["dP"], kunci["dQ"], kunci["qInv"])

            if not m_val == m_rsa == m_crt:
                raise ValueError("Verifikasi dekripsi gagal; periksa kandidat yang lolos Miller-Rabin.")
            st.success("Perhitungan berhasil; kedua hasil dekripsi cocok dengan pesan asli.")

            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.metric("Pesan Asli (M)", str(m_val))
            with col_res2:
                st.metric("Ciphertext (C)", str(c))
            with col_res3:
                st.metric("Hasil Dekripsi (RSA / CRT)", f"{m_rsa} / {m_crt}")

            st.markdown("---")
            st.subheader("Detail Langkah Matematis")

            # Tahap 1
            with st.expander("1. Pembangkitan Parameter Kunci (Key Generation)", expanded=True):
                col_k1, col_k2 = st.columns(2)
                with col_k1:
                    st.markdown("**Parameter RSA Standar:**")
                    st.latex(rf"n = p \times q = {p_val} \times {q_val} = {kunci['n']}")
                    st.latex(rf"\phi(n) = (p-1)(q-1) = {p_val-1} \times {q_val-1} = {kunci['phi']}")
                    st.latex(rf"e = {kunci['e']}")
                    st.latex(rf"d \equiv e^{{-1}} \pmod{{\phi(n)}} = {kunci['d']}")
                with col_k2:
                    st.markdown("**Parameter Tambahan RSA-CRT:**")
                    st.latex(rf"d_P = d \pmod{{p-1}} = {kunci['d']} \pmod{{{p_val-1}}} = {kunci['dP']}")
                    st.latex(rf"d_Q = d \pmod{{q-1}} = {kunci['d']} \pmod{{{q_val-1}}} = {kunci['dQ']}")
                    st.latex(rf"q_{{inv}} = q^{{-1}} \pmod p = {q_val}^{{-1}} \pmod{{{p_val}}} = {kunci['qInv']}")

            # Tahap 2
            with st.expander("2. Proses Enkripsi (Encryption)", expanded=True):
                st.markdown("Ciphertext dihitung dengan pemangkatan modular:")
                st.latex(rf"C = M^e \pmod n = {m_val}^{{{kunci['e']}}} \pmod{{{kunci['n']}}} = \mathbf{{{c}}}")

            # Tahap 3
            with st.expander("3. Perbandingan Dekripsi (Decryption)", expanded=True):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.markdown("#### Dekripsi RSA Standar")
                    st.markdown("Melakukan 1 pemangkatan modular dengan modulus besar $n$ dan eksponen $d$:")
                    st.latex(rf"M = C^d \pmod n")
                    st.latex(rf"M = {c}^{{{kunci['d']}}} \pmod{{{kunci['n']}}} = \mathbf{{{m_rsa}}}")
                with col_d2:
                    st.markdown("#### Dekripsi RSA-CRT (Garner's Algorithm)")
                    m1 = rsa.pangkat_modular(c, kunci["dP"], p_val)
                    m2 = rsa.pangkat_modular(c, kunci["dQ"], q_val)
                    h = (kunci["qInv"] * (m1 - m2)) % p_val

                    st.markdown("1. Hitung sisa pada sub-modulus $p$ dan $q$:")
                    st.latex(rf"m_1 = C^{{d_P}} \pmod p = {c}^{{{kunci['dP']}}} \pmod{{{p_val}}} = {m1}")
                    st.latex(rf"m_2 = C^{{d_Q}} \pmod q = {c}^{{{kunci['dQ']}}} \pmod{{{q_val}}} = {m2}")
                    st.markdown("2. Rekombinasi koefisien CRT:")
                    st.latex(rf"h = q_{{inv}} \times (m_1 - m_2) \pmod p = {kunci['qInv']} \times ({m1} - {m2}) \pmod{{{p_val}}} = {h}")
                    st.markdown("3. Rekonstruksi pesan utuh:")
                    st.latex(rf"M = m_2 + h \times q = {m2} + {h} \times {q_val} = \mathbf{{{m_crt}}}")

        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

# ==========================================================
# TAB 2: BENCHMARK & GRAFIK PERFORMA
# ==========================================================
with tab_bench:
    st.header("Benchmark Waktu Dekripsi: RSA vs RSA-CRT")
    st.write(
        "Uji kecepatan pemrosesan dekripsi pada berbagai ukuran panjang bit prima p dan q. "
        "Program menjalankan pemanasan (warmup) dan percobaan berulang dengan urutan bergantian "
        "untuk memastikan hasil median tidak bias."
    )

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        bit_options = st.multiselect(
            "Pilih Panjang Bit Prima (p & q):",
            [64, 128, 256, 512, 1024, 2048],
            default=[256, 512, 1024],
            help="Modulus n akan berukuran sekitar 2x bit ini (misal 512 bit untuk prima 256 bit)."
        )
    with col_b2:
        trials_count = st.slider("Jumlah Percobaan (Trials):", min_value=5, max_value=100, value=30, step=5)
        warmup_count = st.slider("Jumlah Pemanasan (Warmup):", min_value=1, max_value=10, value=3, step=1)
    with col_b3:
        bench_message = st.text_input("Pesan Uji M:", value="1819")
        bench_mr = st.slider("Ronde Miller-Rabin:", min_value=5, max_value=30, value=20, step=5)

    if st.button("Mulai Benchmark", type="primary", use_container_width=True):
        if not bit_options:
            st.warning("Pilih minimal satu ukuran bit prima untuk diuji.")
            st.stop()

        try:
            bench_message = int(bench_message)
        except ValueError:
            st.error("Pesan M harus berupa bilangan bulat desimal.")
            st.stop()

        hasil_list = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, bit in enumerate(bit_options):
            status_text.markdown(f"Sedang memproses panjang prima {bit} bit... (Membangkitkan prima & menguji dekripsi)")
            t_start = time.perf_counter()
            kunci = rsa.kunci_acak(bit, bench_mr, 65537)
            res = rsa.benchmark(kunci, bench_message, trials_count, warmup_count, bench_mr)
            hasil_list.append(res)
            progress_bar.progress((idx + 1) / len(bit_options))

        status_text.success("Benchmark selesai untuk semua ukuran bit!")
        progress_bar.empty()

        # Simpan CSV ke disk
        csv_path = rsa.simpan_csv(hasil_list)

        # Siapkan DataFrame
        df = pd.DataFrame(hasil_list)
        df_display = df[[
            "bit_p", "bit_kunci", "iterasi",
            "rsa_median_ms", "crt_median_ms",
            "rsa_rerata_ms", "crt_rerata_ms",
            "speedup", "status"
        ]].copy()
        df_display.columns = [
            "Bit p/q", "Bit Kunci (n)", "Percobaan",
            "RSA Median (ms)", "CRT Median (ms)",
            "RSA Rerata (ms)", "CRT Rerata (ms)",
            "Rasio Speedup (x)", "Status"
        ]

        # Metric Cards Highlights
        st.subheader("Ringkasan Hasil")
        cols_metric = st.columns(len(hasil_list))
        for i, item in enumerate(hasil_list):
            with cols_metric[i]:
                st.metric(
                    label=f"Kunci {item['bit_kunci']} bit (p={item['bit_p']}b)",
                    value=f"{item['speedup']:.2f}x (RSA/CRT)",
                    delta=f"RSA {item['rsa_median_ms']:.3f} ms vs CRT {item['crt_median_ms']:.3f} ms",
                    delta_color="inverse",
                )

        st.markdown("---")
        st.subheader("Visualisasi Grafik Performa")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("**Perbandingan Median Waktu Dekripsi (ms)** *(Lebih rendah = lebih cepat)*")
            chart_df = df[["bit_kunci", "rsa_median_ms", "crt_median_ms"]].copy()
            chart_df["Label"] = chart_df["bit_kunci"].apply(lambda b: f"{b} bit")
            chart_df = chart_df.set_index("Label")[["rsa_median_ms", "crt_median_ms"]]
            chart_df.columns = ["RSA Standar (ms)", "RSA-CRT (ms)"]
            st.bar_chart(chart_df)

        with col_g2:
            st.markdown("**Rasio Percepatan CRT (Speedup Factor)** *(Berapa kali lipat CRT lebih cepat)*")
            speedup_df = df[["bit_kunci", "speedup"]].copy()
            speedup_df["Label"] = speedup_df["bit_kunci"].apply(lambda b: f"{b} bit")
            speedup_df = speedup_df.set_index("Label")[["speedup"]]
            speedup_df.columns = ["Speedup (x)"]
            st.line_chart(speedup_df)

        st.markdown("---")
        st.subheader("Tabel Metrik Lengkap")
        st.dataframe(df_display, use_container_width=True)

        # Download button CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Unduh Hasil Benchmark (.CSV)",
            data=csv_buffer.getvalue(),
            file_name="benchmark_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ==========================================================
# TAB 3: VERIFIKASI KASUS UJI (TEST SUITE)
# ==========================================================
with tab_test:
    st.header("Verifikasi Otomatis Kasus Uji (Test Suite)")
    st.write(
        "Menjalankan 16 pengujian otomatis yang mencakup 6 kasus valid (V1-V6) "
        "dan 10 kasus penolakan input tidak valid (I1-I10) sesuai dokumen rancangan pengujian."
    )

    if st.button("Jalankan 16 Kasus Uji Otomatis", type="primary", use_container_width=True):
        st.info("Memulai eksekusi pengujian suite...")
        
        cases = test_runner.jalankan_suite()
        hasil_uji = [{"ID": case["id"], "Tipe": case["tipe"], "Input": case["input"],
                      "Ekspektasi": case["ekspektasi"], "Status": case["status"],
                      "Keterangan": case["keterangan"]} for case in cases]
        lulus_count = sum(case["status"] == "PASS" for case in cases)
        gagal_count = len(cases) - lulus_count
        show_summary = st.success if gagal_count == 0 else st.error
        show_summary(f"Rekapitulasi: **{lulus_count} / {len(cases)} PASS**, **{gagal_count} FAIL**")

        df_test = pd.DataFrame(hasil_uji)
        
        def color_status(val):
            color = '#28a745' if val == 'PASS' else '#dc3545'
            return f'color: white; background-color: {color}; font-weight: bold; text-align: center;'

        st.dataframe(
            df_test.style.map(color_status, subset=['Status']),
            use_container_width=True
        )