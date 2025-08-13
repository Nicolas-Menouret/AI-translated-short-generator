import sys
from pathlib import Path

import streamlit as st
import yaml

sys.path.append(str(Path(__file__).resolve().parents[2]))
from src.core.setup import setup_dirs

# Setup directories
raw_videos_dir, musics_dir, transcripts_dir, subtitle_styles_dir, shorts_dir = (
    setup_dirs()
)

# Page configuration
st.title("🎬 Subtitles Configuration")
st.write("Customize your subtitle styles")


def config_name_component():

    st.header("Subtitle Style Configuration")

    # Initialize session state
    if "current_config" not in st.session_state:
        st.session_state.current_config = {
            "ass_parameters": {
                "fontname": "Impact",
                "fontsize": 0.06,
                "PrimaryColour": "&H00FFFFFF",
                "SecondaryColour": "&H00000000",
                "OutlineColour": "&H00000000",
                "BackColour": "&H64000000",
                "BorderStyle": 1,
                "Outline": 3,
                "Shadow": 2,
                "MarginL": 10,
                "MarginR": 10,
                "MarginV": 0.2,
                "Alignment": "bottom-middle",
            },
            "special_effects": {
                "zoom_in": False,
                "box_highlight": False,
                "color_highlight": False,
                "karaoke_highlight": False,
            },
            "subtitles_parameters": {
                "max_words": 3,
                "max_length": 20,
                "upper_case": False,
            },
        }
        st.session_state.config_name = "new_config"

    config_name = st.text_input(
        "Configuration Name:",
        value=st.session_state.config_name,
        key="config_name_input",
    )
    st.caption(
        "Give your configuration a descriptive name (e.g., 'Classic_White', 'Bold_Yellow', 'Minimal_Black')"
    )


def save_subtitle_config(config_name, config_data):
    """Save subtitle configuration to YAML file"""
    config_dir = subtitle_styles_dir
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / f"{config_name}.yaml"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {e}")
        return False


def save_subtitle_config_component():
    if st.button("💾 Save Configuration", type="primary", use_container_width=True):
        if (
            st.session_state.config_name_input
            and st.session_state.config_name_input.strip()
        ):
            if save_subtitle_config(
                st.session_state.config_name_input.strip(),
                st.session_state.current_config,
            ):
                st.success(
                    f"Configuration '{st.session_state.config_name_input.strip()}' saved successfully!"
                )
                st.info(
                    "💡 **Next Steps**: Your configuration is now saved and can be used in video generation. Go to the Manual Generation or Automatic Generation pages to apply this subtitle style to your videos!"
                )
                st.rerun()
        else:
            st.error("Please enter a configuration name!")

    # Add save information
    st.caption(
        f"💾 **Save Info**: Configurations are saved as YAML files in the '{subtitle_styles_dir}' folder and are automatically available for use in video generation."
    )


def ass_parameters_component():
    """Handle ASS parameters configuration"""
    st.subheader("ASS Parameters")
    ass_params = st.session_state.current_config["ass_parameters"]

    # Row 1: Colors
    st.write("**Colors**")
    col1a, col2a, col3a, col4a = st.columns(4)

    with col1a:
        ass_params["PrimaryColour"] = st.color_picker(
            "Primary Color:", value="#FFFFFF", key="primary_color"
        )
        st.caption("Main text color - choose a bright color for readability")
        # Convert hex to ASS format
        if ass_params["PrimaryColour"].startswith("#"):
            hex_color = ass_params["PrimaryColour"][1:]
            ass_params["PrimaryColour"] = (
                f"&H00{hex_color[4:6].upper()}{hex_color[2:4].upper()}{hex_color[0:2].upper()}"
            )

    with col2a:
        ass_params["SecondaryColour"] = st.color_picker(
            "Secondary Color:", value="#000000", key="secondary_color"
        )
        st.caption("Used for secondary text effects and transitions")
        if ass_params["SecondaryColour"].startswith("#"):
            hex_color = ass_params["SecondaryColour"][1:]
            ass_params["SecondaryColour"] = (
                f"&H00{hex_color[4:6].upper()}{hex_color[2:4].upper()}{hex_color[0:2].upper()}"
            )

    with col3a:
        ass_params["OutlineColour"] = st.color_picker(
            "Outline Color:", value="#000000", key="outline_color"
        )
        st.caption("Color of text outline - usually black for contrast")
        if ass_params["OutlineColour"].startswith("#"):
            hex_color = ass_params["OutlineColour"][1:]
            ass_params["OutlineColour"] = (
                f"&H00{hex_color[4:6].upper()}{hex_color[2:4].upper()}{hex_color[0:2].upper()}"
            )

    with col4a:
        ass_params["BackColour"] = st.color_picker(
            "Background Color:", value="#000000", key="back_color"
        )
        st.caption("Background behind text - often semi-transparent")
        if ass_params["BackColour"].startswith("#"):
            hex_color = ass_params["BackColour"][1:]
            ass_params["BackColour"] = (
                f"&H64{hex_color[4:6]}{hex_color[2:4]}{hex_color[0:2]}"
            )

    # Row 2: Font & Layout
    st.write("**Font & Layout**")
    col1b, col2b, col3b, col4b = st.columns(4)

    with col1b:
        ass_params["fontname"] = st.selectbox(
            "Font Name:",
            ["Impact", "Arial", "Helvetica", "Times New Roman", "Verdana"],
            index=["Impact", "Arial", "Helvetica", "Times New Roman", "Verdana"].index(
                ass_params.get("fontname", "Impact")
            ),
        )
        st.caption("Choose a readable font - Impact is popular for videos")

    with col2b:
        ass_params["fontsize"] = st.number_input(
            "Font Size (% of video height):",
            min_value=0.01,
            max_value=0.2,
            value=float(ass_params.get("fontsize", 0.06)),
            step=0.01,
            format="%.3f",
        )
        st.caption("0.01-0.2 (1%-20% of video height) - 0.06 (6%) recommended")

    with col3b:
        ass_params["BorderStyle"] = st.selectbox(
            "Border Style:",
            [1, 3],
            index=[1, 3].index(ass_params.get("BorderStyle", 1)),
        )
        st.caption("1=outline+shadow, 3=box around text")

    with col4b:
        alignment_options = {
            "bottom-middle": "Bottom Center (recommended)",
            "bottom-left": "Bottom Left",
            "bottom-right": "Bottom Right",
            "top-left": "Top Left",
            "top-right": "Top Right",
            "top-middle": "Top Center",
            "middle-left": "Middle Left",
            "middle-right": "Middle Right",
            "middle-middle": "Center",
        }
        selected_alignment = st.selectbox(
            "Alignment:",
            list(alignment_options.keys()),
            index=list(alignment_options.keys()).index(
                ass_params.get("Alignment", "bottom-middle")
            ),
        )
        ass_params["Alignment"] = selected_alignment
        st.caption(f"How is the text aligned on the screen")

    # Row 3: Margins
    st.write("**Margins**")
    col1c, col2c, col3c = st.columns(3)

    with col1c:
        ass_params["MarginL"] = st.number_input(
            "Left Margin:",
            min_value=0,
            max_value=100,
            value=ass_params.get("MarginL", 10),
            step=1,
        )
        st.caption("Distance from left edge (0-100)")

    with col2c:
        ass_params["MarginR"] = st.number_input(
            "Right Margin:",
            min_value=0,
            max_value=100,
            value=ass_params.get("MarginR", 10),
            step=1,
        )
        st.caption("Distance from right edge (0-100)")

    with col3c:
        ass_params["MarginV"] = st.number_input(
            "Vertical Margin (% of video height):",
            min_value=0.0,
            max_value=1.0,
            value=float(ass_params.get("MarginV", 0.2)),
            step=0.01,
            format="%.2f",
        )
        st.caption("0.0-1.0 (0%-100% of video height) - 0.2 (20%) recommended")

    # Row 4: Outline and Shadow
    st.write("**Outline & Shadow**")
    col1d, col2d = st.columns(2)

    with col1d:
        ass_params["Outline"] = st.slider(
            "Outline Width:",
            min_value=0,
            max_value=10,
            value=ass_params.get("Outline", 3),
            step=1,
        )
        st.caption("Text outline thickness (2-4px recommended)")

    with col2d:
        ass_params["Shadow"] = st.slider(
            "Shadow Depth:",
            min_value=0,
            max_value=10,
            value=ass_params.get("Shadow", 2),
            step=1,
        )
        st.caption("Shadow distance (0-4px works well)")


def special_effects_component():
    """Handle special effects configuration"""
    st.subheader("Special Effects (Select maximum 1 effect)")
    special_effects = st.session_state.current_config["special_effects"]

    # Row 5: Special Effects
    col1e, col2e, col3e, col4e = st.columns(4)

    with col1e:
        special_effects["zoom_in"] = st.checkbox(
            "Zoom In Effect", value=special_effects.get("zoom_in", False)
        )
        st.caption("Dynamic zoom animation on subtitle appearance")

    with col2e:
        special_effects["box_highlight"] = st.checkbox(
            "Box Highlight", value=special_effects.get("box_highlight", False)
        )
        st.caption("Draw colored box around subtitle text")

    with col3e:
        special_effects["color_highlight"] = st.checkbox(
            "Color Highlight", value=special_effects.get("color_highlight", False)
        )
        st.caption("Dynamic color changes during subtitle display")

    with col4e:
        special_effects["karaoke_highlight"] = st.checkbox(
            "Karaoke Highlight", value=special_effects.get("karaoke_highlight", False)
        )
        st.caption("Word-by-word highlighting like karaoke lyrics")


def subtitles_parameters_component():
    """Handle subtitles parameters configuration"""
    st.subheader("Subtitles Parameters")
    subtitles_params = st.session_state.current_config["subtitles_parameters"]

    # Row 6: Subtitles Parameters
    col1f, col2f, col3f = st.columns(3)

    with col1f:
        subtitles_params["max_words"] = st.number_input(
            "Max Words per Line:",
            min_value=1,
            max_value=10,
            value=subtitles_params.get("max_words", 3),
            step=1,
        )
        st.caption("Limit words per subtitle line for readability")

    with col2f:
        subtitles_params["max_length"] = st.number_input(
            "Max Characters per Line:",
            min_value=10,
            max_value=50,
            value=subtitles_params.get("max_length", 20),
            step=1,
        )
        st.caption("Character limit per line (20-30 recommended)")

    with col3f:
        st.write("")
        subtitles_params["upper_case"] = st.checkbox(
            "Convert to Uppercase", value=subtitles_params.get("upper_case", False)
        )
        st.caption("Transform all text to uppercase for emphasis")


if __name__ == "__main__":

    config_name_component()

    st.divider()

    ass_parameters_component()

    st.divider()

    subtitles_parameters_component()

    st.divider()

    special_effects_component()

    st.divider()

    save_subtitle_config_component()
