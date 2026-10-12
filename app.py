from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="สถิติผู้ป่วยโรงพยาบาล", page_icon="🏥", layout="wide")

DATA_FILE = Path(__file__).parent / "data.csv"
REQUIRED_COLUMNS = {
    "YEAR", "REGION", "SIZE_HOSPITAL", "TYPE_PATIENT", "NUMBER_PATIENTS"
}


@st.cache_data
def load_data(file_path: Path) -> pd.DataFrame:
    """Load and normalize the hospital patient dataset."""
    data = pd.read_csv(file_path)
    data.columns = data.columns.str.strip()
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError("คอลัมน์ใน data.csv ไม่ครบ: " + ", ".join(sorted(missing_columns)))
    for column in ("REGION", "SIZE_HOSPITAL", "TYPE_PATIENT", "UNIT", "SOURCE"):
        if column in data.columns:
            data[column] = data[column].astype("string").str.strip()
    data["YEAR"] = pd.to_numeric(data["YEAR"], errors="coerce")
    data["NUMBER_PATIENTS"] = pd.to_numeric(data["NUMBER_PATIENTS"], errors="coerce")
    data = data.dropna(subset=list(REQUIRED_COLUMNS))
    data["YEAR"] = data["YEAR"].astype(int)
    return data


st.title("🏥 สถิติผู้ป่วยโรงพยาบาล")
st.write(
    "สำรวจจำนวนผู้ป่วยตามปี ภูมิภาค ประเภทผู้ป่วย และขนาดโรงพยาบาล "
    "โดยใช้ข้อมูลจากสำนักงานสถิติแห่งชาติ"
)

try:
    df = load_data(DATA_FILE)
except FileNotFoundError:
    st.error("ไม่พบไฟล์ data.csv กรุณาวางไฟล์ไว้ในโฟลเดอร์เดียวกับ app.py")
    st.stop()
except (OSError, pd.errors.ParserError, ValueError, KeyError) as error:
    st.error(f"อ่านหรือจัดรูปแบบข้อมูลไม่สำเร็จ: {error}")
    st.stop()

if df.empty:
    st.warning("ไม่มีข้อมูลที่พร้อมใช้งานใน data.csv กรุณาตรวจสอบข้อมูลในไฟล์")
    st.stop()

regions = sorted(df["REGION"].dropna().unique().tolist())
patient_types = sorted(df["TYPE_PATIENT"].dropna().unique().tolist())
with st.sidebar:
    st.header("ตัวกรองข้อมูล")
    default_region = "ทั่วราชอาณาจักร" if "ทั่วราชอาณาจักร" in regions else regions[0]
    selected_region = st.selectbox(
        "ภูมิภาค", regions, index=regions.index(default_region)
    )
    default_type = "รวม" if "รวม" in patient_types else patient_types[0]
    selected_type = st.selectbox(
        "ประเภทผู้ป่วย", patient_types, index=patient_types.index(default_type)
    )

region_data = df[
    (df["REGION"] == selected_region) & (df["TYPE_PATIENT"] == selected_type)
].copy()

if region_data.empty:
    st.info("ไม่มีข้อมูลตามตัวกรองที่เลือก")
    st.stop()

years = sorted(region_data["YEAR"].unique().tolist())
with st.sidebar:
    selected_year = st.selectbox(
        "ปีที่ใช้เปรียบเทียบขนาดโรงพยาบาล (พ.ศ.)", years, index=len(years) - 1
    )
    st.caption("เลือกภูมิภาคเดียวเพื่อไม่รวมยอดทั้งประเทศซ้ำกับยอดรายภูมิภาค")

yearly_totals = (
    region_data.groupby("YEAR", as_index=False)["NUMBER_PATIENTS"]
    .sum()
    .sort_values("YEAR")
)
selected_year_data = region_data[region_data["YEAR"] == selected_year]
size_totals = (
    selected_year_data.groupby("SIZE_HOSPITAL", as_index=False)["NUMBER_PATIENTS"]
    .sum()
    .sort_values("NUMBER_PATIENTS", ascending=False)
)

metric1, metric2, metric3 = st.columns(3)
metric1.metric("ภูมิภาค", selected_region)
metric2.metric("ประเภทผู้ป่วย", selected_type)
metric3.metric("จำนวนผู้ป่วยในปีที่เลือก", f"{int(selected_year_data['NUMBER_PATIENTS'].sum()):,} คน")

st.subheader("📈 แนวโน้มจำนวนผู้ป่วยตามปี")
st.caption("รวมจำนวนผู้ป่วยทุกขนาดโรงพยาบาลภายในภูมิภาคและประเภทผู้ป่วยที่เลือก")
yearly_chart = yearly_totals.rename(columns={"YEAR": "ปี พ.ศ.", "NUMBER_PATIENTS": "จำนวนผู้ป่วย (คน)"})
yearly_chart["ปี พ.ศ."] = yearly_chart["ปี พ.ศ."].astype(str)
st.line_chart(yearly_chart.set_index("ปี พ.ศ.")["จำนวนผู้ป่วย (คน)"])
st.caption("แสดงเฉพาะปีที่มีในชุดข้อมูล: " + ", ".join(str(year) for year in years))

st.subheader(f"📊 จำนวนผู้ป่วยแยกตามขนาดโรงพยาบาล ปี {selected_year}")
size_chart = size_totals.rename(columns={"SIZE_HOSPITAL": "ขนาดโรงพยาบาล", "NUMBER_PATIENTS": "จำนวนผู้ป่วย (คน)"})
st.bar_chart(size_chart.set_index("ขนาดโรงพยาบาล")["จำนวนผู้ป่วย (คน)"])

with st.expander("ดูตารางข้อมูลที่ใช้ในกราฟ"):
    st.dataframe(
        region_data.sort_values(["YEAR", "SIZE_HOSPITAL"]),
        width="stretch",
        hide_index=True,
    )

sources = ", ".join(df["SOURCE"].dropna().unique().tolist()) if "SOURCE" in df else "ไม่ระบุ"
st.caption(f"แหล่งข้อมูล: {sources} · หน่วย: คน")
