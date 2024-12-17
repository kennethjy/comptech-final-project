import tkinter as tk
from tkinter import messagebox
from logic import grammar, text_to_midi2, text_to_array


def create_visual_grid(frame):
    """
    Displays all the symbols and their visual box representation in a horizontal layout.
    """
    # Clear the frame first
    for widget in frame.winfo_children():
        widget.destroy()

    column = 0  # Start placing sections from the first column
    for category, tokens in grammar.items():
        if isinstance(tokens, dict):  # Only process tokens that have patterns
            # Create a frame for each section
            section_frame = tk.Frame(frame)
            section_frame.grid(row=0, column=column, padx=20, pady=10)  # Place each section in a new column

            # Display the category name
            tk.Label(section_frame, text=category, font=("Arial", 14, "bold")).pack(anchor="w", pady=5)

            # Display symbols and their visual patterns
            for symbol, pattern in tokens.items():
                row_frame = tk.Frame(section_frame)
                row_frame.pack(anchor="w", pady=2)

                # Display the symbol
                tk.Label(row_frame, text=f"{symbol}:", font=("Arial", 12)).pack(side="left", padx=5)

                # Display the visual representation of the pattern
                for value in pattern:
                    color = "black" if value == 1 else "white"
                    tk.Label(row_frame, bg=color, width=2, height=1, relief="solid").pack(side="left", padx=1)

            column += 1  # Move to the next column for the next section


def log_message(message, is_error=False):
    """
    Logs a message to the console box.
    """
    console_box.config(state="normal")  # Enable editing to append
    console_box.insert(tk.END, message + "\n")
    console_box.see(tk.END)  # Auto-scroll to the latest log
    if is_error:
        console_box.tag_add("error", "end-2l", "end-1l")
        console_box.tag_config("error", foreground="red")
    console_box.config(state="disabled")  # Disable editing to prevent user input

def draw_visual_preview(data):
    """
    Render the array of arrays as a visual preview with 0s and 1s.
    Includes zoom functionality with mouse scroll.
    """
    preview_window = tk.Toplevel()
    preview_window.title("Visual Preview")

    # Set initial window size
    preview_window.geometry("800x800")

    # Initial zoom factor
    zoom_factor = tk.DoubleVar(value=1.0)

    # Frame for the canvas and scrollbars
    canvas_frame = tk.Frame(preview_window)
    canvas_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(canvas_frame, bg="white")
    h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
    v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

    # Pack canvas and scrollbars
    canvas.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    canvas_frame.grid_rowconfigure(0, weight=1)
    canvas_frame.grid_columnconfigure(0, weight=1)

    def redraw_canvas():
        """
        Redraw the canvas based on the current zoom factor.
        """
        canvas.delete("all")  # Clear previous drawing

        box_size = int(20 * zoom_factor.get())  # Scale box size
        x_start, y_start = 10, 10
        y_offset = 0

        for section in data:
            x_offset = 0
            # Rotate the visual representation (values flipped)
            for value in section:
                if value == 1:
                    # Draw a filled black box for '1'
                    canvas.create_rectangle(
                        y_start + y_offset,
                        x_start + x_offset,
                        y_start + y_offset + box_size,
                        x_start + x_offset + box_size,
                        fill="black", outline="black", width=2
                    )
                elif value == 0:
                    # Draw a hollow box for '0'
                    canvas.create_rectangle(
                        y_start + y_offset,
                        x_start + x_offset,
                        y_start + y_offset + box_size,
                        x_start + x_offset + box_size,
                        outline="black", width=2
                    )
                x_offset += box_size  # Adjust spacing between boxes
            y_offset += box_size  # Adjust spacing for newlines

        # Update the scroll region to fit the new content
        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    # Initial draw
    redraw_canvas()

    # Function to handle zooming with mouse scroll
    def on_zoom(event):
        """
        Zoom in or out when the mouse wheel is scrolled.
        """
        if event.delta > 0:
            # Scroll up -> zoom in
            zoom_factor.set(min(zoom_factor.get() + 0.1, 3.0))  # Max zoom of 3x
        elif event.delta < 0:
            # Scroll down -> zoom out
            zoom_factor.set(max(zoom_factor.get() - 0.1, 0.5))  # Min zoom of 0.5x
        redraw_canvas()

    # Bind Ctrl + Mouse Scroll to zoom
    canvas.bind("<Control-MouseWheel>", on_zoom)



def preview_midi_conversion():
    input_text = input_field.get()

    if not input_text:
        log_message("Error: Input field cannot be empty.", is_error=True)
        return

    try:
        visual_data = text_to_array(input_text, logger=log_message)
        draw_visual_preview(visual_data)
    except Exception as e:
        log_message(str(e), is_error=True)

def run_midi_conversion():
    input_text = input_field.get()
    file_name = file_name_field.get().strip()

    if not input_text:
        log_message("Error: Input field cannot be empty.", is_error=True)
        return

    if not file_name:
        log_message("Error: File name field cannot be empty.", is_error=True)
        return

    if not file_name.endswith(".mid"):
        file_name += ".mid"

    try:
        # Pass the log_message function as the logger to text_to_midi2
        text_to_midi2(input_text, output_file=file_name, logger=log_message)
    except Exception as e:
        log_message(f"An unexpected error occurred: {e}", is_error=True)


# Main Tkinter setup
root = tk.Tk()
root.title("Text to MIDI Converter with Symbol Visualizer")

# Top frame for the visual representation
visual_frame = tk.Frame(root)
visual_frame.grid(row=0, column=0, columnspan=2, pady=10)

# Create the visual grid
create_visual_grid(visual_frame)

# Console box for displaying logs
console_frame = tk.Frame(root)
console_frame.grid(row=1, column=0, columnspan=2, pady=10, padx=10)
console_box = tk.Text(console_frame, height=10, width=80, state="disabled", wrap="word", bg="lightgrey")
console_box.pack(side="left", fill="both", expand=True)
scrollbar = tk.Scrollbar(console_frame, command=console_box.yview)
scrollbar.pack(side="right", fill="y")
console_box.config(yscrollcommand=scrollbar.set)

# Bottom frame for input fields and button
input_frame = tk.Frame(root)
input_frame.grid(row=2, column=0, columnspan=2, pady=10)

# Input for the MIDI string
tk.Label(input_frame, text="Enter your input string:").grid(row=0, column=0, padx=5, sticky="e")
input_field = tk.Entry(input_frame, width=50)
input_field.grid(row=0, column=1, padx=5)

# Input for the file name
tk.Label(input_frame, text="Enter file name:").grid(row=1, column=0, padx=5, sticky="e")
file_name_field = tk.Entry(input_frame, width=50)
file_name_field.grid(row=1, column=1, padx=5)

# Frame for buttons
button_frame = tk.Frame(input_frame)
button_frame.grid(row=2, column=0, columnspan=2, pady=10)

# Preview button
preview_button = tk.Button(button_frame, text="Preview", command=preview_midi_conversion)
preview_button.pack(side="left", padx=5)

# Submit button
submit_button = tk.Button(button_frame, text="Convert to MIDI", command=run_midi_conversion)
submit_button.pack(side="left", padx=5)

# Run the Tkinter loop
root.mainloop()