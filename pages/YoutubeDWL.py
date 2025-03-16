from dash import html, dcc, callback, Output, Input, State
import dash
import os
import re
import subprocess
import tempfile
import uuid
import shutil
from dash.exceptions import PreventUpdate

# Register this page
dash.register_page(__name__, path='/youtube-downloader', name="YouTube Downloader", title="YouTube Downloader")

# Create a directory for downloaded files
DOWNLOAD_DIRECTORY = os.path.join(tempfile.gettempdir(), 'dash_youtube_downloader')
if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

# Global state to track processing
state = {
    'is_processing': False,
    'available_formats': {},
    'current_url': None,
    'format_info': ''
}

def is_valid_url(url):
    """Check if the URL is valid."""
    pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be|twitch\.tv|soundcloud\.com|vimeo\.com|dailymotion\.com)/.+'
    return bool(re.match(pattern, url))

def get_available_formats(url):
    """Get available formats using yt-dlp"""
    try:
        command = [
            'yt-dlp',
            '-U',
            '--list-formats',
            '--no-check-certificate',
            url
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Error fetching formats: {result.stderr}", {}
            
        # Parse the output to extract available formats
        output = result.stdout
        
        # Create format objects with codec info and bitrate
        video_formats = []
        audio_formats = []
        combined_formats = []
        
        for line in output.split('\n'):
            if not line.strip() or 'format code' in line.lower() or '---' in line:
                continue
                
            # Parse format information with regular expressions
            format_id_match = re.search(r'^(\S+)', line)
            if not format_id_match:
                continue
                
            format_id = format_id_match.group(1)
            
            # Extract extension
            ext_match = re.search(r'\s+(\w+)\s+', line)
            ext = ext_match.group(1) if ext_match else 'unknown'
            
            # Extract resolution for video formats
            resolution_match = re.search(r'(\d+x\d+)', line)
            resolution = resolution_match.group(1) if resolution_match else 'unknown'
            
            # Extract fps if available
            fps_match = re.search(r'(\d+)\s+fps', line)
            fps = int(fps_match.group(1)) if fps_match else 30
            
            # Extract file size or estimate
            filesize_match = re.search(r'(\d+\.\d+)(?:Ki|Mi|Gi)B', line)
            filesize = filesize_match.group(1) if filesize_match else '0'
            
            # Extract bitrate
            bitrate_match = re.search(r'(\d+)k\s+(\d+)k', line)  # For "ABR kbps ASR"
            if bitrate_match:
                bitrate = bitrate_match.group(1)
            else:
                bitrate_match = re.search(r'(\d+)k\s', line)
                bitrate = bitrate_match.group(1) if bitrate_match else '0'
            
            # Extract codec info
            vcodec_match = re.search(r'(avc1\.\w+|vp9|vp\d+\.\d+\.\d+\.\d+)', line)
            vcodec = vcodec_match.group(1) if vcodec_match else 'unknown'
            
            acodec_match = re.search(r'(mp4a\.\d+\.\d+|opus|vorbis|mp3)', line)
            acodec = acodec_match.group(1) if acodec_match else 'unknown'
            
            # Extract height from resolution for quality sorting
            height = 0
            if 'x' in resolution:
                try:
                    height = int(resolution.split('x')[1])
                except:
                    pass
                    
            # Create a format object with all the details
            format_obj = {
                'id': format_id,
                'ext': ext,
                'resolution': resolution,
                'height': height,
                'fps': fps,
                'filesize': float(filesize),
                'bitrate': int(bitrate) if bitrate.isdigit() else 0,
                'vcodec': vcodec,
                'acodec': acodec,
                'line': line
            }
            
            # Categorize based on format type
            if 'video only' in line:
                video_formats.append(format_obj)
            elif 'audio only' in line:
                audio_formats.append(format_obj)
            else:
                combined_formats.append(format_obj)
        
        # Process formats into more usable structures
        formats = {
            'video': {},  # Will contain ext -> resolution -> codec -> formats
            'audio': {},  # Will contain ext -> bitrate -> codec -> formats
            'raw_video': video_formats,
            'raw_audio': audio_formats,
            'raw_combined': combined_formats
        }
        
        # Process video formats: Group by ext, then resolution, then codec
        for vid_format in video_formats:
            ext = vid_format['ext']
            height = vid_format['height']
            fps = vid_format['fps']
            vcodec = vid_format['vcodec']
            
            if vcodec == 'unknown':
                vcodec = 'other'
                
            # Create a resolution key including fps for high frame rates
            resolution_key = f"{height}p"
            if fps > 30:
                resolution_key = f"{height}p{fps}"
            
            # Initialize nested dictionaries if they don't exist
            if ext not in formats['video']:
                formats['video'][ext] = {}
            
            if resolution_key not in formats['video'][ext]:
                formats['video'][ext][resolution_key] = {}
                
            if vcodec not in formats['video'][ext][resolution_key]:
                formats['video'][ext][resolution_key][vcodec] = []
                
            formats['video'][ext][resolution_key][vcodec].append(vid_format)
        
        # Process audio formats
        for audio_format in audio_formats:
            ext = audio_format['ext']
            bitrate = audio_format['bitrate']
            acodec = audio_format['acodec']
            
            # Bitrate key
            bitrate_key = f"{bitrate}k"
            
            # Initialize nested dictionaries if they don't exist
            if ext not in formats['audio']:
                formats['audio'][ext] = {}
            
            if bitrate_key not in formats['audio'][ext]:
                formats['audio'][ext][bitrate_key] = {}
                
            if acodec not in formats['audio'][ext][bitrate_key]:
                formats['audio'][ext][bitrate_key][acodec] = []
                
            formats['audio'][ext][bitrate_key][acodec].append(audio_format)
        
        # Process combined formats too
        formats['combined'] = combined_formats
                
        return output, formats
        
    except Exception as e:
        return f"Exception getting formats: {str(e)}", {}

def build_format_options(formats):
    """Build options for dropdown menus from format data"""
    if not formats:
        return {
            'video': {'label': 'Video', 'formats': {}},
            'audio': {'label': 'Audio', 'formats': {}}
        }
    
    # Create structure for dropdowns
    result = {
        'video': {
            'label': 'Video',
            'formats': {},
            'resolutions': {},
            'codecs': {}
        },
        'audio': {
            'label': 'Audio',
            'formats': {},
            'bitrates': {},
            'codecs': {}
        }
    }
    
    # Process video formats
    if 'video' in formats:
        # Get available extensions
        exts = sorted(formats['video'].keys())
        
        # For each extension, get available resolutions and codecs
        for ext in exts:
            if ext not in result['video']['formats']:
                result['video']['formats'][ext] = {}
                
            # Sort resolutions by height
            resolutions = sorted(
                formats['video'][ext].keys(), 
                key=lambda x: int(re.search(r'(\d+)', x).group(1)), 
                reverse=True
            )
            
            valid_formats_for_ext = False
            
            for resolution in resolutions:
                if resolution not in result['video']['formats'][ext]:
                    result['video']['formats'][ext][resolution] = {}
                
                # Get available codecs for this resolution (excluding unknown)
                codecs = [c for c in sorted(formats['video'][ext][resolution].keys()) if c != 'unknown' and c != 'other']
                
                if codecs:  # Only process if we have valid codecs
                    valid_formats_for_ext = True
                    
                    for codec in codecs:
                        format_info = formats['video'][ext][resolution][codec][0]  # Take first format
                        format_id = format_info['id']
                        
                        # Add to formats dictionary
                        result['video']['formats'][ext][resolution][codec] = {
                            'label': f"{codec}",
                            'value': format_id,
                            'info': format_info
                        }
                        
                        # Add to resolution and codec dictionaries for dropdown options
                        if resolution not in result['video']['resolutions']:
                            result['video']['resolutions'][resolution] = {
                                'label': resolution,
                                'value': resolution
                            }
                        
                        if codec not in result['video']['codecs']:
                            result['video']['codecs'][codec] = {
                                'label': codec,
                                'value': codec
                            }
            
            # Remove extension if it has no valid formats
            if not valid_formats_for_ext:
                del result['video']['formats'][ext]
    
    # Process audio formats
    if 'audio' in formats:
        # Get available extensions
        exts = sorted(formats['audio'].keys())
        
        # For each extension, get available bitrates and codecs
        for ext in exts:
            if ext not in result['audio']['formats']:
                result['audio']['formats'][ext] = {}
                
            # Sort bitrates numerically (from highest to lowest)
            bitrates = sorted(
                formats['audio'][ext].keys(), 
                key=lambda x: int(re.search(r'(\d+)', x).group(1)), 
                reverse=True
            )
            
            valid_formats_for_ext = False
            
            for bitrate in bitrates:
                if bitrate not in result['audio']['formats'][ext]:
                    result['audio']['formats'][ext][bitrate] = {}
                
                # Get available codecs for this bitrate (excluding unknown)
                codecs = [c for c in sorted(formats['audio'][ext][bitrate].keys()) if c != 'unknown' and c != 'other']
                
                if codecs:  # Only process if we have valid codecs
                    valid_formats_for_ext = True
                    
                    for codec in codecs:
                        format_info = formats['audio'][ext][bitrate][codec][0]  # Take first format
                        format_id = format_info['id']
                        
                        # Add to formats dictionary
                        result['audio']['formats'][ext][bitrate][codec] = {
                            'label': f"{codec}",
                            'value': format_id,
                            'info': format_info
                        }
                        
                        # Add to bitrate and codec dictionaries for dropdown options
                        if bitrate not in result['audio']['bitrates']:
                            result['audio']['bitrates'][bitrate] = {
                                'label': bitrate,
                                'value': bitrate
                            }
                        
                        if codec not in result['audio']['codecs']:
                            result['audio']['codecs'][codec] = {
                                'label': codec,
                                'value': codec
                            }
            
            # Remove extension if it has no valid formats
            if not valid_formats_for_ext:
                del result['audio']['formats'][ext]
    
    return result

# Clean up old downloads
def clean_old_downloads(except_id=None):
    for folder_name in os.listdir(DOWNLOAD_DIRECTORY):
        if except_id and folder_name == except_id:
            continue
        folder_path = os.path.join(DOWNLOAD_DIRECTORY, folder_name)
        if os.path.isdir(folder_path):
            try:
                shutil.rmtree(folder_path)
            except Exception as e:
                print(f"Error removing old download {folder_path}: {e}")

# Add this new function to get video/audio info
def get_media_info(url):
    """Get thumbnail URL and title for the video/audio"""
    try:
        command = [
            'yt-dlp',
            '-J',  # Output as JSON
            '--no-playlist',
            '--skip-download',
            url
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            return None, None
            
        import json
        data = json.loads(result.stdout)
        
        thumbnail_url = None
        title = data.get('title', 'Unknown Title')       
        
        # Try to get the best thumbnail
        thumbnails = data.get('thumbnails', [])
        if thumbnails:
            # Sort by resolution and get the highest quality
            thumbnails.sort(key=lambda x: x.get('height', 0) * x.get('width', 0), reverse=True)
            thumbnail_url = thumbnails[0].get('url')
        
        return thumbnail_url, title
    except Exception as e:
        print(f"Error getting media info: {str(e)}")
        return None, None

# Layout for the YouTube Downloader page - update the format selection panel and button containers
layout = html.Div([
    
    html.Div([
        html.Div([
            # Center the URL input and button
            html.Div([
                html.Label("Enter Video URL:", style={"marginBottom": "5px", "textAlign": "center", "width": "100%"}),
                html.Div([
                    dcc.Input(
                        id="url-input",
                        type="text",
                        placeholder="https://www.youtube.com/watch?v=...",
                        style={"width": "300px", "marginBottom": "10px", "marginRight": "10px"}
                    ),
                    
                    # Fixed-width container for the button
                    html.Div([
                        html.Button(
                            "Analyze URL",
                            id="analyze-button",
                            className="button primary-button",
                            style={"width": "120px", "marginBottom": "10px"}
                        ),
                    ], style={"width": "120px", "display": "inline-block"}),
                    
                    # Fixed width and height for the spinner container with placeholder
                    html.Div(
                        id="loading-container-analyze",
                        children=[
                            html.Div(
                                className="loader",
                                style={"visibility": "hidden"}  # Reserve space but hide initially
                            )
                        ],
                        style={
                            "width": "30px",
                            "height": "30px",
                            "display": "inline-flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "marginLeft": "10px"
                        }
                    ),
                ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"}),
            ], style={"textAlign": "center"}),
            
            html.Div(id="analysis-status", style={"marginTop": "5px", "color": "#2196F3", "fontStyle": "italic", "textAlign": "center"}),
            html.Div(id="error-message", style={"color": "red", "marginTop": "10px", "textAlign": "center"})
        ], className="card", style={"marginBottom": "20px"}),
        
        # Format selection panel - Fix the dropdown alignment
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Media Type:"),
                    dcc.Dropdown(
                        id="media-type-dropdown",
                        options=[],
                        clearable=False,
                        style={"width": "100%", "color": "black"}
                    ),
                ], style={"flex": "1", "paddingRight": "10px"}),  # Use flex: 1 instead of fixed width
                
                html.Div([
                    html.Label("Format:"),
                    dcc.Dropdown(
                        id="format-dropdown",
                        options=[],
                        clearable=False,
                        style={"width": "100%", "color": "black"}
                    ),
                ], style={"flex": "1", "paddingRight": "10px"}),
                
                html.Div([
                    # Dynamic label that will be updated based on media type
                    html.Label(id="resolution-bitrate-label", children="Resolution/Bitrate:"),
                    dcc.Dropdown(
                        id="resolution-dropdown",
                        options=[],
                        clearable=False,
                        style={"width": "100%", "color": "black"}
                    ),
                ], style={"flex": "1", "paddingRight": "10px"}),
                
                html.Div([
                    html.Label("Codec:"),
                    dcc.Dropdown(
                        id="codec-dropdown",
                        options=[],
                        clearable=False,
                        style={"width": "100%", "color": "black"}
                    ),
                ], style={"flex": "1"}),
            ], style={
                "marginBottom": "15px",
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "gap": "10px"
            }),
            
            # Fixed layout for process button and spinner
            html.Div([
                html.Div([
                    html.Button(
                        "Process Video",
                        id="process-button",
                        className="button primary-button",
                        style={"width": "150px", "marginBottom": "10px"}
                    ),
                ], style={"width": "150px", "display": "inline-block"}),
                
                # Fixed position for process spinner
                html.Div(
                    id="loading-container-process",
                    children=[
                        html.Div(
                            className="loader",
                            style={"visibility": "hidden"}  # Reserve space but hide initially
                        )
                    ],
                    style={
                        "width": "30px",
                        "height": "30px",
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "marginLeft": "10px"
                    }
                ),
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "15px"}),
        ], id="format-selection-panel", style={"display": "none"}),
        
        # Progress indicator
        html.Div(id="progress-indicator", style={"marginTop": "10px", "fontWeight": "bold", "color": "#3498db", "display": "none"}),
        
        # Status message (hidden)
        html.Div(id="status-message", style={"display": "none"}),
        
        # Download link container
        html.Div(id="download-link-container"),
        
        # Move media info container after download section and center it
        html.Div(id="media-info-container", style={"display": "none", "marginTop": "30px", "textAlign": "center"}, children=[
            html.Div([
                # Center the thumbnail and title
                html.Div([
                    html.H3(id="media-title", style={"margin": "0 0 15px 0"}),
                    html.Div(id="thumbnail-container"),
                ], style={"display": "flex", "flexDirection": "column", "alignItems": "center"})
            ], style={"display": "flex", "justifyContent": "center"})
        ]),
        
        # Store for video info
        dcc.Store(id="video-data")
    ]),
    
    # Replace html.Style with a properly supported way to add styles
    html.Div(
        style={"display": "none"},  # Hide this div
        id="spinner-styles",
        children=[]
    )
], style={
    # Add the spinner styles directly to the parent div's style dictionary
    "cssText": """
        .loader {
            border: 5px solid #f3f3f3;
            border-radius: 50%;
            border-top: 5px solid #3498db;
            width: 25px;
            height: 25px;
            animation: spin 2s linear infinite;
            display: inline-block;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Style for disabled button */
        .button-disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
    """
})

# Add a callback to update the resolution/bitrate label based on media type
@callback(
    Output("resolution-bitrate-label", "children"),
    [Input("media-type-dropdown", "value")],
    prevent_initial_call=True
)
def update_resolution_bitrate_label(media_type):
    if media_type == "audio":
        return "Bitrate:"
    else:
        return "Resolution:"

# Analyze URL and show available formats - also get media info
@callback(
    [Output("format-selection-panel", "style"),
     Output("analysis-status", "children"),
     Output("media-type-dropdown", "options"),
     Output("media-type-dropdown", "value"),
     Output("error-message", "children", allow_duplicate=True),
     Output("video-data", "data"),
     Output("loading-container-analyze", "children"),  # For the spinner
     Output("analyze-button", "disabled"),  # For button state
     Output("analyze-button", "style"),     # For button appearance
     Output("download-link-container", "children", allow_duplicate=True),
     Output("media-info-container", "style"),
     Output("thumbnail-container", "children"),
     Output("media-title", "children")
    ],
    [Input("analyze-button", "n_clicks")],
    [State("url-input", "value")],
    prevent_initial_call=True
)
def analyze_url(n_clicks, url):
    if not n_clicks or n_clicks is None:
        raise PreventUpdate
    
    # Start with spinner and disabled button
    spinner = html.Div(className="loader")
    button_disabled = True
    button_style = {"width": "120px", "opacity": "0.6", "cursor": "not-allowed"}
    
    if not url:
        return {"display": "none"}, "", [], None, "Please enter a URL", {}, \
               [], False, {"width": "120px"}, [], \
               {"display": "none"}, [], ""
    
    if not is_valid_url(url):
        return {"display": "none"}, "", [], None, "Invalid URL. Please enter a valid video/audio URL", {}, \
               "", False, {"width": "120px"}, [], \
               {"display": "none"}, [], ""
    
    # Reset current URL if different
    if state['current_url'] != url:
        state['current_url'] = url
        state['available_formats'] = {}
    
    try:
        # Get media info (thumbnail and title)
        thumbnail_url, title = get_media_info(url)
        
        # Create thumbnail element - ensure it's always a list, never None
        thumbnail_element = []
        if thumbnail_url:
            thumbnail_element = [html.Img(src=thumbnail_url, style={
                "maxWidth": "100%", 
                "maxHeight": "300px",
                "borderRadius": "5px",
                "margin": "0 auto"
            })]
        
        # Get available formats
        format_info, formats = get_available_formats(url)
        state['format_info'] = format_info
        
        # Build format options based on available formats
        media_types = build_format_options(formats)
        state['available_formats'] = media_types
        
        # Check if we have any video or audio formats
        has_video = 'video' in media_types and media_types['video']['formats']
        has_audio = 'audio' in media_types and media_types['audio']['formats']
        
        # Create media type options - ensure it's always a list, never None
        options = []
        if has_video:
            options.append({'label': 'Video', 'value': 'video'})
        if has_audio:
            options.append({'label': 'Audio', 'value': 'audio'})
        
        if not options:
            return {"display": "none"}, "", [], None, "No valid formats found for this URL. Try another URL.", {}, \
                   "", False, {"width": "120px"}, [], \
                   {"display": "none"}, [], ""
        
        # Set default value
        default_value = 'video' if has_video else 'audio'
        
        # Show the media info container if we have at least title or thumbnail
        media_info_style = {"display": "block", "marginTop": "30px", "textAlign": "center"} if title or thumbnail_url else {"display": "none"}
        
        # Make sure title is always a string
        title = title or ""  # Convert None to empty string if needed
        
        # Clear the download container when analyzing a new URL
        return {"display": "block"}, "", options, default_value, "", media_types, \
               [html.Div(className="loader", style={"visibility": "hidden"})], \
               False, {"width": "120px"}, [], \
               media_info_style, thumbnail_element, title
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        # Error case: Reset button state
        button_disabled = False
        button_style = {"width": "120px"}
        
        return {"display": "none"}, "", [], None, f"Error analyzing URL: {str(e)}", {}, \
               [html.Div(className="loader", style={"visibility": "hidden"})], \
               False, {"width": "120px"}, [], \
               {"display": "none"}, [], ""

# Update format options based on media type selection
@callback(
    [Output("format-dropdown", "options"),
     Output("format-dropdown", "value")],
    [Input("media-type-dropdown", "value")],
    [State("video-data", "data")],
    prevent_initial_call=True
)
def update_format_options(media_type, video_data):
    if not video_data or not media_type or media_type not in video_data:
        return [], None
    
    formats = video_data[media_type]['formats']
    options = [{'label': ext.upper(), 'value': ext} for ext in formats.keys()]
    
    if not options:
        return [], None
    
    # Default to first format
    default_format = next(iter(formats.keys()))
    return options, default_format

# Update resolution/bitrate options
@callback(
    [Output("resolution-dropdown", "options"),
     Output("resolution-dropdown", "value")],
    [Input("media-type-dropdown", "value"),
     Input("format-dropdown", "value")],
    [State("video-data", "data")],
    prevent_initial_call=True
)
def update_resolution_options(media_type, format_ext, video_data):
    if not video_data or not media_type or not format_ext:
        return [], None
    
    if (media_type in video_data and 
        format_ext in video_data[media_type]['formats']):
        
        if media_type == 'video':
            # Get resolutions for this format
            resolutions = video_data[media_type]['formats'][format_ext].keys()
            options = [{'label': res, 'value': res} for res in resolutions]
            
            if not options:
                return [], None
            
            # Default to highest resolution
            default_res = list(resolutions)[0] if resolutions else None
            return options, default_res
            
        elif media_type == 'audio':
            # Get bitrates for this format
            bitrates = video_data[media_type]['formats'][format_ext].keys()
            options = [{'label': bitrate, 'value': bitrate} for bitrate in bitrates]
            
            if not options:
                return [], None
            
            # Default to highest bitrate
            default_bitrate = list(bitrates)[0] if bitrates else None
            return options, default_bitrate
    
    return [], None

# Update codec options
@callback(
    [Output("codec-dropdown", "options"),
     Output("codec-dropdown", "value")],
    [Input("media-type-dropdown", "value"),
     Input("format-dropdown", "value"),
     Input("resolution-dropdown", "value")],
    [State("video-data", "data")],
    prevent_initial_call=True
)
def update_codec_options(media_type, format_ext, resolution_or_bitrate, video_data):
    if not video_data or not media_type or not format_ext or not resolution_or_bitrate:
        return [], None
    
    if (media_type in video_data and 
        format_ext in video_data[media_type]['formats'] and
        resolution_or_bitrate in video_data[media_type]['formats'][format_ext]):
        
        codecs = video_data[media_type]['formats'][format_ext][resolution_or_bitrate].keys()
        options = [{'label': codec, 'value': codec} for codec in codecs]
        
        if not options:
            return [], None
        
        # Default to first codec
        default_codec = list(codecs)[0] if codecs else None
        return options, default_codec
    
    return [], None

# Add a callback to update the Process button text based on media type
@callback(
    Output("process-button", "children"),
    [Input("media-type-dropdown", "value")],
    prevent_initial_call=True
)
def update_process_button_text(media_type):
    if media_type == "audio":
        return "Process Audio"
    else:
        return "Process Video"

# Process and download video - fix audio issues
@callback(
    [Output("status-message", "children"),
     Output("error-message", "children", allow_duplicate=True),
     Output("download-link-container", "children"),
     Output("progress-indicator", "children"),
     Output("progress-indicator", "style"),
     Output("loading-container-process", "children"),
     Output("process-button", "disabled"),
     Output("process-button", "style")
    ],
    [Input("process-button", "n_clicks")],
    [State("url-input", "value"),
     State("media-type-dropdown", "value"),
     State("format-dropdown", "value"),
     State("resolution-dropdown", "value"),
     State("codec-dropdown", "value"),
     State("video-data", "data")],
    prevent_initial_call=True
)
def process_video(n_clicks, url, media_type, format_ext, resolution_or_bitrate, codec, video_data):
    if not n_clicks or state['is_processing']:
        raise PreventUpdate
    
    # Set processing flag
    state['is_processing'] = True
    
    # Start with spinner and disabled button
    spinner = html.Div(className="loader")
    button_disabled = True
    button_style = {"width": "150px", "opacity": "0.6", "cursor": "not-allowed"}
    
    progress_message = "Processing has started... Please wait while we prepare your file."
    progress_style = {'marginTop': '10px', 'fontWeight': 'bold', 'color': '#3498db', 'display': 'block'}
    
    if not url or not media_type or not format_ext or not resolution_or_bitrate or not codec:
        state['is_processing'] = False
        return "", "Missing required information. Please complete all fields.", "", progress_message, {"display": "none"}, \
               [], False, {"width": "150px"}
    
    try:
        # Get the format ID
        format_id = None
        
        # Navigate the nested structure to get the format ID
        if (media_type in video_data and 
            format_ext in video_data[media_type]['formats'] and 
            resolution_or_bitrate in video_data[media_type]['formats'][format_ext] and
            codec in video_data[media_type]['formats'][format_ext][resolution_or_bitrate]):
            
            format_info = video_data[media_type]['formats'][format_ext][resolution_or_bitrate][codec]
            format_id = format_info['value']
        
        if not format_id:
            state['is_processing'] = False
            return "", "Could not determine format ID. Try analyzing the URL again.", "", progress_message, {"display": "none"}, \
                   [], False, {"width": "150px"}
        
        # Create a unique subfolder
        download_id = str(uuid.uuid4())
        download_path = os.path.join(DOWNLOAD_DIRECTORY, download_id)
        os.makedirs(download_path, exist_ok=True)
        
        # Construct filename template
        output_template = os.path.join(download_path, '%(title)s.%(ext)s')
        
        # Run yt-dlp command with format ID
        if media_type == 'audio':
            # For audio, ensure we get an audio file with proper format
            command = [
                'yt-dlp',
                '-f', format_id,
                '-o', output_template,
                '--no-playlist',
                '--max-filesize', '1G',
                '--extract-audio', 
                '--audio-format', 'mp3', 
                '--audio-quality', '0'
            ]
        else:
            # For video, ensure we get both video and audio with proper encoding
            # Fix the audio encoding issues by using explicit parameters
            command = [
                'yt-dlp',
                # Use m4a audio explicitly to prevent opus usage
                '-f', f"{format_id}+bestaudio[ext=m4a]/best",
                '-o', output_template,
                '--no-playlist',
                '--max-filesize', '1G',
                '--merge-output-format', 'mp4',
                # Force AAC audio codec for compatibility with MP4
                '--audio-format', 'aac',
                # Pass FFmpeg arguments directly to ensure AAC audio encoding
                '--postprocessor-args', '-c:a aac -b:a 192k',
                # Prefer FFmpeg for more reliable conversion
                '--prefer-ffmpeg'
            ]
            
        # Add URL
        command.append(url)
        
        # Execute command
        progress_message = "Downloading and processing... This may take a few minutes."
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Handle any errors
        if result.returncode != 0:
            state['is_processing'] = False
            if "File is larger than max-filesize" in result.stderr:
                return "", "Error: File exceeds the 1GB size limit", "", "", {'display': 'none'}, \
                       [], False, {"width": "150px"}
            return "", f"Error downloading: {result.stderr}", "", "", {'display': 'none'}, \
                   [], False, {"width": "150px"}
        
        # Find the downloaded file
        files = os.listdir(download_path)
        if not files:
            state['is_processing'] = False
            return "", "Download failed: No file was created", "", "", {'display': 'none'}, \
                   [], False, {"width": "150px"}
        
        filename = files[0]
        file_path = os.path.join(download_path, filename)
        
        # Clean up old downloads except current one
        clean_old_downloads(except_id=download_id)
        
        # Create a download button with the file ID instead of a link
        download_button = html.Div([
            html.Button(
                # Update text based on media type
                f'Download {"Audio" if media_type == "audio" else "Video"} ({round(os.path.getsize(file_path) / (1024 * 1024), 2)} MB)',
                id='download-button',
                style={
                    'display': 'block',
                    'margin': '20px auto',
                    'padding': '10px 20px',
                    'background': '#4CAF50',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '5px',
                    'width': 'fit-content',
                    'fontSize': '16px',
                    'cursor': 'pointer'
                }
            ),
            dcc.Store(id='download-info', data={
                'path': file_path,
                'filename': filename
            }),
            dcc.Download(id='download-handler')
        ])
        
        # Remove the "Download ready!" text by setting to empty string
        status_message = ""
        
        # Reset processing flag
        state['is_processing'] = False
        button_disabled = False
        button_style = {"width": "150px"}
        
        return status_message, "", download_button, "", {'display': 'none'}, \
               [html.Div(className="loader", style={"visibility": "hidden"})], \
               False, {"width": "150px"}
    
    except Exception as e:
        state['is_processing'] = False
        print(f"Error in process_video: {str(e)}")
        button_disabled = False
        button_style = {"width": "150px"}
        
        return "", f"An error occurred: {str(e)}", "", "", {'display': 'none'}, \
               [html.Div(className="loader", style={"visibility": "hidden"})], \
               False, {"width": "150px"}

# Add a callback to handle the file download using Dash's built-in download component
@callback(
    Output('download-handler', 'data'),
    Input('download-button', 'n_clicks'),
    State('download-info', 'data'),
    prevent_initial_call=True
)
def download_video_file(n_clicks, download_info):
    if not n_clicks or not download_info:
        raise PreventUpdate
    
    try:
        file_path = download_info['path']
        filename = download_info['filename']
        
        if not os.path.exists(file_path):
            raise PreventUpdate
        
        # Return the file as downloadable content
        return dcc.send_file(file_path, filename=filename)
        
    except Exception as e:
        print(f"Error in download_video_file: {str(e)}")
        raise PreventUpdate

# Remove the Flask route - it won't work with Dash pages
# @dash.callback_context.app.server.route("/download/<download_id>/<filename>")
# def download_file(download_id, filename):
#     path = os.path.join(DOWNLOAD_DIRECTORY, download_id)
#     from flask import send_from_directory
#     return send_from_directory(path, filename, as_attachment=True)

# Fix the styles callback
dash.clientside_callback(
    """
    function(id) {
        try {
            if (!document.getElementById('youtube-dwl-styles')) {
                var style = document.createElement('style');
                style.id = 'youtube-dwl-styles';
                style.textContent = `
                    .spinner {
                        border: 4px solid rgba(0, 0, 0, 0.1);
                        width: 24px;
                        height: 24px;
                        border-radius: 50%;
                        border-left: 4px solid #2196F3;
                        animation: spin 1s linear infinite;
                    }
                    
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    
                    .button-disabled {
                        opacity: 0.6;
                        cursor: not-allowed;
                    }
                    
                    .loader {
                        border: 5px solid #f3f3f3;
                        border-radius: 50%;
                        border-top: 5px solid #3498db;
                        width: 25px;
                        height: 25px;
                        animation: spin 2s linear infinite;
                        display: inline-block;
                    }
                `;
                document.head.appendChild(style);
            }
            return [];
        } catch (e) {
            console.error("Error in style injection callback:", e);
            return [];
        }
    }
    """,
    Output("spinner-styles", "children"),
    Input("spinner-styles", "id"),
)

# Replace the clientside callbacks for loading spinners with server-side pattern callbacks

# Add separate server-side callbacks to handle the spinner display
@callback(
    Output("loading-container-analyze", "children", allow_duplicate=True),
    Input("analyze-button", "n_clicks"),
    prevent_initial_call=True
)
def show_analyze_spinner(n_clicks):
    if not n_clicks:
        return [
            html.Div(
                className="loader",
                style={"visibility": "hidden"}
            )
        ]
    return [
        html.Div(
            className="loader",
            style={"visibility": "visible"}
        )
    ]

@callback(
    Output("loading-container-process", "children", allow_duplicate=True),
    Input("process-button", "n_clicks"),
    prevent_initial_call=True
)
def show_process_spinner(n_clicks):
    if not n_clicks:
        return [
            html.Div(
                className="loader",
                style={"visibility": "hidden"}
            )
        ]
    return [
        html.Div(
            className="loader",
            style={"visibility": "visible"}
        )
    ]

