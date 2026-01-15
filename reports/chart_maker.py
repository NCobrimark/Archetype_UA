import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List
import io

def create_radar_chart(scores: Dict[str, int]) -> io.BytesIO:
    """
    Generates a radar chart from archetype scores.
    Returns: BytesIO object containing the image.
    """
    labels = list(scores.keys())
    values = list(scores.values())
    
    # Number of variables
    num_vars = len(labels)
    
    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    
    # Close the plot
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    ax.fill(angles, values, color='#1E90FF', alpha=0.25)
    ax.plot(angles, values, color='#1E90FF', linewidth=2)
    
    # Labels
    # Convert labels to Ukrainian names, handling both strings and Enums
    from core.models import ArchetypeType
    display_labels = []
    for arch_key in labels:
        try:
            # If it's already an Enum member or a string that matches one
            arch_enum = ArchetypeType(arch_key) if isinstance(arch_key, str) else arch_key
            # Use format: "Укр (Eng)"
            name_uk = arch_enum.ukrainian_name.split(' (')[0]
            name_en = arch_enum.value # Enum value is the English name
            display_labels.append(f"{name_uk}\n({name_en})")
        except Exception:
            display_labels.append(str(arch_key))

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(display_labels, fontsize=8)
    
    # Y-labels options
    ax.set_yticklabels([]) # Hide radial labels for cleanliness?
    # Or show specific ranges like 0, 10, 20.
    
    plt.title("Your Archetype Profile", y=1.08)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    
    return buf
