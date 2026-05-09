from pathlib import Path
import pandas as pd
import streamlit as st
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent

COUNT_RESULTS = ROOT / "outputs" / "counting_batch_refined_xmlgt" / "count_results.csv"
COUNT_SUMMARY = ROOT / "outputs" / "counting_batch_refined_xmlgt" / "count_summary.txt"

OVERLAY_DIR = ROOT / "outputs" / "counting_batch_refined_xmlgt" / "overlays"
PRED_MASK_DIR = ROOT / "outputs" / "counting_batch_refined_xmlgt" / "pred_masks"
DENSITY_DIR = ROOT / "outputs" / "density_maps"

MORPH_RESULTS = ROOT / "outputs" / "morphology" / "morphology_results.csv"
MORPH_SUMMARY = ROOT / "outputs" / "morphology" / "morphology_summary.csv"

ALL_CSV = ROOT / "data" / "splits" / "all.csv"


st.set_page_config(
    page_title="Nuclei Segmentation Prototype",
    layout="wide"
)


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        st.error(f"Missing file: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_text(path: Path) -> str:
    if not path.exists():
        return f"Missing file: {path}"
    return path.read_text(encoding="utf-8", errors="ignore")


def find_original_image(image_name: str) -> Path | None:
    if not ALL_CSV.exists():
        return None

    df = pd.read_csv(ALL_CSV)

    if "image_path" not in df.columns:
        return None

    matches = df[df["image_path"].astype(str).str.contains(image_name, regex=False)]

    if len(matches) == 0:
        return None

    image_path = Path(matches.iloc[0]["image_path"])

    if not image_path.is_absolute():
        image_path = ROOT / image_path

    if image_path.exists():
        return image_path

    return None


def show_image(path: Path, caption: str):
    if path.exists():
        image = Image.open(path)
        st.image(image, caption=caption, width="stretch")
    else:
        st.warning(f"Missing image: {path.name}")


def main():
    st.title("AI-Based Cell Nuclei Segmentation and Counting Prototype")

    st.markdown(
        """
        This prototype integrates the corrected nuclei counting pipeline, predicted masks,
        overlay visualizations, density heatmaps, and morphology measurements.
        """
    )

    st.info(
        "Corrected baseline: Threshold = 0.8, MIN_AREA = 1 for counting, "
        "XML-based ground truth. Morphology uses MIN_AREA = 5 for stable shape measurements."
    )

    count_df = load_csv(COUNT_RESULTS)
    morph_df = load_csv(MORPH_RESULTS)
    morph_summary_df = load_csv(MORPH_SUMMARY)

    if count_df.empty:
        st.stop()

    image_names = sorted(count_df["image_name"].unique().tolist())

    selected_image = st.sidebar.selectbox(
        "Select microscopy image",
        image_names
    )

    selected_count = count_df[count_df["image_name"] == selected_image].iloc[0]

    st.sidebar.markdown("## Current Image Metrics")
    st.sidebar.write(f"Predicted count: **{selected_count['predicted_count']}**")
    st.sidebar.write(f"Ground truth count: **{selected_count['ground_truth_count']}**")
    st.sidebar.write(f"Absolute error: **{selected_count['absolute_error']}**")
    st.sidebar.write(f"Squared error: **{selected_count['squared_error']}**")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Overview",
            "Visual Outputs",
            "Counting Results",
            "Morphology",
            "Project Summary"
        ]
    )

    with tab1:
        st.header("Prototype Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Processed Images", len(count_df))

        with col2:
            st.metric("Average MAE", f"{count_df['absolute_error'].mean():.4f}")

        with col3:
            st.metric("Average MSE", f"{count_df['squared_error'].mean():.4f}")

        with col4:
            st.metric("Selected Image Error", int(selected_count["absolute_error"]))

        st.subheader("Selected Image")
        st.dataframe(
            count_df[count_df["image_name"] == selected_image],
            width="stretch"
        )

    with tab2:
        st.header("Visual Outputs")

        original_path = find_original_image(selected_image)
        overlay_path = OVERLAY_DIR / f"{selected_image}_overlay.png"
        pred_mask_path = PRED_MASK_DIR / f"{selected_image}_pred_mask.png"
        density_path = DENSITY_DIR / f"{selected_image}_density_heatmap.png"

        col1, col2 = st.columns(2)

        with col1:
            if original_path is not None:
                show_image(original_path, "Original Microscopy Image")
            else:
                st.warning("Original image path was not found from all.csv.")

        with col2:
            show_image(overlay_path, "Overlay Visualization")

        col3, col4 = st.columns(2)

        with col3:
            show_image(pred_mask_path, "Predicted Nuclei Mask")

        with col4:
            show_image(density_path, "Density Heatmap")

    with tab3:
        st.header("Counting Results")

        st.subheader("Full Count Table")
        st.dataframe(count_df, width="stretch")

        csv_data = count_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download count_results.csv",
            data=csv_data,
            file_name="count_results.csv",
            mime="text/csv"
        )

        st.subheader("Best 10 Cases by Absolute Error")
        best_df = count_df.sort_values("absolute_error").head(10)
        st.dataframe(best_df, width="stretch")

        st.subheader("Worst 10 Cases by Absolute Error")
        worst_df = count_df.sort_values("absolute_error", ascending=False).head(10)
        st.dataframe(worst_df, width="stretch")

    with tab4:
        st.header("Morphology Features")

        if morph_summary_df.empty or morph_df.empty:
            st.warning("Morphology files are missing or empty.")
        else:
            st.subheader("Image-Level Morphology Summary")
            selected_morph_summary = morph_summary_df[
                morph_summary_df["image_name"] == selected_image
            ]
            st.dataframe(selected_morph_summary, width="stretch")

            st.subheader("Object-Level Morphology Features")
            selected_morph = morph_df[morph_df["image_name"] == selected_image]
            st.dataframe(selected_morph.head(100), width="stretch")

            morph_csv = selected_morph.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download selected image morphology CSV",
                data=morph_csv,
                file_name=f"{selected_image}_morphology.csv",
                mime="text/csv"
            )

    with tab5:
        st.header("Project Summary")

        st.subheader("Corrected Counting Summary")
        st.code(load_text(COUNT_SUMMARY))

        st.subheader("Current Interpretation")
        st.markdown(
            """
            The system now provides a prototype-level workflow:

            **Input microscopy image → predicted mask → overlay → count estimate → density heatmap → morphology table → dashboard review**

            The main limitation remains instance separation in dense nuclei regions.
            Connected-components counting under-counts when many nuclei are touching or merged.
            """
        )

        st.subheader("Final Deliverables Supported")
        st.markdown(
            """
            - Predicted nuclei masks  
            - Overlay visualizations  
            - Corrected XML-based counting evaluation  
            - Density heatmaps  
            - Morphology measurements  
            - Exportable CSV outputs  
            - Interactive prototype interface  
            """
        )


if __name__ == "__main__":
    main()
