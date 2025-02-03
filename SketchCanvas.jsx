import React, { useEffect, useState } from "react";
import { FabricJSCanvas, useFabricJSEditor } from "fabricjs-react";
import "../css/SketchCanvas.css";

function DrawingCanvas() {
    const { editor, onReady } = useFabricJSEditor(); // Get the editor instance
    const [color, setColor] = useState("#35363a"); // Brush color
    const [isDrawing, setIsDrawing] = useState(false); // Controls drawing mode
    const [generatedImage, setGeneratedImage] = useState(null); // Store the generated image
    const [isGenerating, setIsGenerating] = useState(false); // Controls spinner visibility

    // Initialize canvas
    useEffect(() => {
        if (!editor) return;

        editor.canvas.setHeight(500);
        editor.canvas.setWidth(500);
        editor.canvas.freeDrawingBrush.width = 5;
        editor.canvas.renderAll();
    }, [editor]);

    // Update brush color
    useEffect(() => {
        if (!editor) return;
        editor.canvas.freeDrawingBrush.color = color;
    }, [color, editor]);

    // Toggle drawing mode
    const toggleDraw = () => {
        if (!editor) return;
        const newDrawingMode = !isDrawing;
        editor.canvas.isDrawingMode = newDrawingMode;
        setIsDrawing(newDrawingMode);
    };

    // Toggle spinner visibility
    const toggleSpinner = () => {
      setIsGenerating((prev) => !prev);
  };
  
    // Clear canvas
    const clear = () => {
        if (!editor) return;
        editor.canvas.clear();
    };

    async function GenerateImage() {
        if (!editor) {
            console.error("Editor is not initialized.");
            return;
        }

        // Show spinner
        toggleSpinner();

        try {
            // Convert canvas to Base64 image
            const data = editor.canvas.toDataURL("image/png");

            // Prepare the payload (Remove the "data:image/png;base64," prefix)
            const payload = JSON.stringify({
                image_b64: data.split(",")[1],
            });

            // Send the image to FastAPI
            const endpoint ="http://127.0.0.1:8000/upload-image/"

            const response = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: payload,
            });

            if (!response.ok) {
                throw new Error(`Failed to upload image: ${response.statusText}`);
            }

            // Extract the base64-encoded image from the result
            const result = await response.json();
            const base64Image = result.image_generated;
            console.log("base64Image:", base64Image);

            // Store the generated image in state
            setGeneratedImage(`data:image/png;base64,${base64Image}`);
            
        } catch (error) {
            console.error("Error sending image:", error);
            
        }finally {
        toggleSpinner(); // Hide spinner when done
        }
    }

    return (
              // Show spinner while generating the image

      <div>
  
      
      {isGenerating ? (
    <div style={{ textAlign: "center", margin: "20px" }}>
        <div className="spinner"></div>
        <p>Generating...</p>
    </div>) 
        // Show the canvas when not generating
    : !generatedImage ? 
      (<>
        <div className="Canvas" style={{ marginBottom: "10px" }}>
            <button className="Start-Stop-btn" onClick={toggleDraw}>
                {isDrawing ? "Stop Drawing" : "Start Drawing"}
            </button>
            <button className="clear-btn" onClick={clear}>Clear</button>
            <input className="color-selector" style={{ backgroundColor: color }} type="color" value={color} onChange={(e) => setColor(e.target.value)} />
        </div>
          <div style={{ border: "1px solid black", width: "500px", height: "500px" }}>
              <FabricJSCanvas className="canvas" onReady={onReady} />
              <button  style={{ margin: "15px" }} onClick={GenerateImage}>
                  Generate Image
              </button>
          </div>
        </>
      ) 
      : 
      (
          // Show Generated Image When Available
          <div>
              <h3>Generated Image:</h3>
              <img src={generatedImage} alt="Generated" style={{ maxWidth: "100%"}} />
              <div>
              <button onClick={() => window.location.reload()}>Draw again</button>
              </div>          
          </div>
      )}
  </div>
  
    );
}

export default DrawingCanvas;
