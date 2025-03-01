from dash import dcc, html, Input, Output, State, callback
import dash
from dash.exceptions import PreventUpdate
import random
import time

dash.register_page(__name__, path='/sandbox', name="Sandbox")

# Retro theme styles to be applied
retro_styles = {
    'title': {
        'fontFamily': 'arcade, monospace',  # Changed from ArcadeClassic to arcade
        'color': '#FF00FF',  # Bright magenta
        'textShadow': '0 0 10px #FF00FF, 0 0 20px #FF00FF',
        'letterSpacing': '2px',
        'marginBottom': '30px',
        'textAlign': 'center'
    },
    'dropdown': {
        'backgroundColor': '#000',
        'color': '#0F0',  # Bright green
        'border': '2px solid #0F0',
        'borderRadius': '0',
        'fontFamily': 'arcade, monospace',  # Changed from ArcadeClassic to arcade
        'width': '300px',  # Increased width for better visibility
        'zIndex': '100'
    },
    'game_container': {
        'border': '4px solid #00FFFF',  # Cyan
        'borderRadius': '10px',
        'boxShadow': '0 0 20px #00FFFF',
        'backgroundColor': '#000033',  # Dark blue
        'padding': '20px',
        'margin': '30px auto',  # Changed to auto for proper centering
        'maxWidth': '800px',
        'position': 'relative',
        'overflow': 'hidden'
    },
    'button': {
        'fontFamily': 'arcade, monospace',  # Changed from ArcadeClassic to arcade
        'backgroundColor': '#FF0000',  # Red
        'color': 'white',
        'border': '2px solid white',
        'padding': '10px 20px',
        'boxShadow': '0 0 10px #FF0000',
        'cursor': 'pointer',
        'transition': 'all 0.2s',
        'textTransform': 'uppercase',
        'letterSpacing': '2px',
        'display': 'block',
        'margin': '20px auto'
    },
    'game_text': {
        'fontFamily': 'arcade, monospace',  # Changed from ArcadeClassic to arcade
        'color': '#FFFF00',  # Yellow
        'textShadow': '0 0 5px #FFFF00',
        'textAlign': 'center',
        'letterSpacing': '1px'
    }
}

# Create a separate CSS file and use html.Link to include it
head_component = html.Div([
    # Use html.Link to include external CSS files
    html.Link(
        rel='stylesheet',
        href='/assets/sandbox.css'
    ),
    # Additional CSS file for navbar styles
    html.Link(
        rel='stylesheet',
        href='/assets/navbar-override.css'
    )
])

# Game selection dropdown - positioned below navbar but not fixed to screen
game_selector = html.Div([
    dcc.Dropdown(
        id='game-selector',
        options=[
            {'label': 'REACTION TIME TEST', 'value': 'reaction'},
            {'label': 'CURSOR ACCURACY TEST', 'value': 'accuracy'}
        ],
        value='reaction',
        clearable=False,
        style=retro_styles['dropdown']
    )
], style={
    'position': 'absolute',  # Changed from fixed to absolute
    'top': '60px',  # Position below navbar
    'left': '10px',
    'zIndex': '1000'  # Ensure it stays on top
})

# Reaction game content
reaction_game = html.Div([
    html.H3("REACTION TIME TEST", className="arcade-glow", style=retro_styles['title']),
    html.P("CLICK WHEN THE BOX TURNS GREEN!", style=retro_styles['game_text']),
    html.Div(id="reaction-box", style={
        'width': '300px',
        'height': '300px',
        'backgroundColor': '#08519c',
        'borderRadius': '10px',
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
        'cursor': 'pointer',
        'margin': '0 auto',
        'position': 'relative',
        'boxShadow': '0 0 20px #08519c',
        'border': '4px solid #08519c',
    }),
    html.Div(id="reaction-result", className="arcade-glow", style=retro_styles['game_text']),
    html.Button("START", id="start-reaction-test", style=retro_styles['button'])
], id='reaction-game-container', style=retro_styles['game_container'])

# Accuracy game content
accuracy_game = html.Div([
    html.H3("CURSOR ACCURACY TEST", className="arcade-glow", style=retro_styles['title']),
    html.P("HIT THE TARGETS AS FAST AS YOU CAN!", style=retro_styles['game_text']),
    html.Div(id="accuracy-box", style={
        'width': '100%',
        'height': 'calc(100vh - 300px)', # Almost full screen height minus navbar/header
        'minHeight': '400px',
        'backgroundColor': 'rgba(8, 81, 156, 0.3)',
        'borderRadius': '10px',
        'margin': '0 auto',
        'position': 'relative',
        'border': '4px solid #08519c',
    }),
    html.Div(id="accuracy-result", className="arcade-glow", style=retro_styles['game_text']),
    html.Button("START", id="start-accuracy-test", style=retro_styles['button'])
], id='accuracy-game-container', style={**retro_styles['game_container'], 'display': 'none'})

# Custom cursor elements - modified to avoid unwanted purple circle
cursor_elements = html.Div([
    html.Div(className="cursor-dot", style={'display': 'none'}),
    html.Div(className="cursor-trail", style={'display': 'none'})
], id="custom-cursor")

# Update layout to properly center the games and add more retro effects
layout = html.Div([
    # Include head component with CSS
    head_component,
    
    # Custom cursor
    cursor_elements,
    
    # Container to properly position dropdown and game content
    html.Div([
        # Dropdown positioned with absolute position
        game_selector,
        
        # Center-aligned game containers with proper margins and padding
        html.Div([
            reaction_game,
            accuracy_game,
        ], style={'width': '100%', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'marginTop': '80px'})
    ], style={'position': 'relative', 'width': '100%'}),
    
    # Visual effects for retro look - add more 8-bit pixel effects
    html.Div(className="scanlines"),
    html.Div(className="vhs-line-2"),
    html.Div(className="vhs-line-3"),
    html.Div(className="pixel-overlay"),  # Pixel overlay for floating pixels
    html.Div(className="noise-overlay"),  # Static noise effect
    html.Div(className="big-pixels"),     # 8-bit pixel grid
    html.Div(className="grid-lines"),     # Grid lines
    
    # Hidden elements for game state
    dcc.Store(id='reaction-start-time', data=None),
    dcc.Store(id='reaction-state', data='idle'),  # idle, waiting, ready, clicked
    dcc.Store(id='accuracy-state', data='idle'),  # idle, playing
    dcc.Store(id='accuracy-targets', data=[]),
    dcc.Store(id='accuracy-hits', data=0),
    dcc.Store(id='accuracy-misses', data=0),
    dcc.Store(id='accuracy-start-time', data=None),
    dcc.Interval(id='reaction-interval', interval=100, n_intervals=0, disabled=True),
    
    # JavaScript to add sandbox-active class to body and initialize robot functionality
    html.Script('''
    document.addEventListener('DOMContentLoaded', function() {
        document.body.classList.add('sandbox-active');
        
        // Initialize features with proper checks
        if (window.location.pathname.includes('sandbox')) {
            initSandboxFunctionality();
        }
        
        // Add navigation event listeners to reinitialize when needed
        setupNavigationListeners();
    });
    
    // Setup navigation event listeners for SPA navigation
    function setupNavigationListeners() {
        // For History API (SPA navigation)
        const oldPushState = history.pushState;
        history.pushState = function() {
            oldPushState.apply(this, arguments);
            handleUrlChange();
        };
        
        const oldReplaceState = history.replaceState;
        history.replaceState = function() {
            oldReplaceState.apply(this, arguments);
            handleUrlChange();
        };
        
        // For back/forward navigation
        window.addEventListener('popstate', function() {
            handleUrlChange();
        });
        
        // For direct URL changes
        window.addEventListener('DOMContentLoaded', function() {
            handleUrlChange();
        });
    }
    
    // Main function to handle URL changes
    function handleUrlChange() {
        if (window.location.pathname.includes('sandbox')) {
            // We're on the sandbox page
            document.body.classList.add('sandbox-active');
            initSandboxFunctionality();
        } else {
            // We're not on the sandbox page
            removeSandboxStyling();
        }
    }
    
    // Initialize all sandbox page functionality
    function initSandboxFunctionality() {
        // Force init all features with slight delays to ensure DOM is ready
        setTimeout(initRobotFunctionality, 300);
        setTimeout(initCustomCursor, 100);
        setTimeout(initPixelEffects, 200);
    }
    
    // Initialize pixel effects
    function initPixelEffects() {
        const pixelOverlay = document.querySelector('.pixel-overlay');
        if (!pixelOverlay) return;
        
        // Create random pixel blocks
        for (let i = 0; i < 50; i++) {
            const pixel = document.createElement('div');
            pixel.className = 'retro-pixel';
            
            // Random size between 4-12px
            const size = Math.floor(Math.random() * 8) + 4;
            
            // Random position
            const x = Math.floor(Math.random() * window.innerWidth);
            const y = Math.floor(Math.random() * window.innerHeight);
            
            // Random color - 8-bit palette colors
            const colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#FFFFFF'];
            const color = colors[Math.floor(Math.random() * colors.length)];
            
            // Apply styles
            pixel.style.width = size + 'px';
            pixel.style.height = size + 'px';
            pixel.style.left = x + 'px';
            pixel.style.top = y + 'px';
            pixel.style.backgroundColor = color;
            pixel.style.boxShadow = '0 0 ' + (size/2) + 'px ' + color;
            
            // Add floating animation with random duration
            const duration = Math.random() * 10 + 5;
            pixel.style.animation = 'floatPixel ' + duration + 's infinite linear';
            pixel.style.animationDelay = (Math.random() * 5) + 's';
            
            pixelOverlay.appendChild(pixel);
        }
    }
    
    // Initialize custom cursor
    function initCustomCursor() {
        const cursorDot = document.querySelector('.cursor-dot');
        const cursorTrail = document.querySelector('.cursor-trail');
        
        if (!cursorDot || !cursorTrail) {
            setTimeout(initCustomCursor, 100);
            return;
        }
        
        // Show the cursor elements now that we're initializing them
        cursorDot.style.display = 'block';
        cursorTrail.style.display = 'block';
        
        document.addEventListener('mousemove', function(e) {
            // Move main cursor dot
            cursorDot.style.left = e.clientX + 'px';
            cursorDot.style.top = e.clientY + 'px';
            
            // Move trail with delay
            setTimeout(() => {
                cursorTrail.style.left = e.clientX + 'px';
                cursorTrail.style.top = e.clientY + 'px';
            }, 80);
        });
        
        // Add hover effects for interactive elements
        const interactiveElements = document.querySelectorAll('a, button, .box, .nav-link, input, #reaction-box, [id^="target-"]');
        interactiveElements.forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursorDot.style.width = '16px';
                cursorDot.style.height = '16px';
                cursorDot.style.backgroundColor = '#00FF00';
                cursorDot.style.boxShadow = '0 0 15px #00FF00, 0 0 30px #00FF00';
                
                cursorTrail.style.width = '32px';
                cursorTrail.style.height = '32px';
                cursorTrail.style.opacity = '0.8';
            });
            
            el.addEventListener('mouseleave', () => {
                cursorDot.style.width = '12px';
                cursorDot.style.height = '12px';
                cursorDot.style.backgroundColor = '#FF00FF';
                cursorDot.style.boxShadow = '0 0 10px #FF00FF, 0 0 20px #FF00FF';
                
                cursorTrail.style.width = '24px';
                cursorTrail.style.height = '24px';
                cursorTrail.style.opacity = '0.5';
            });
        });
        
        // Show real cursor when outside sandbox page
        document.addEventListener('mouseleave', function() {
            cursorDot.style.display = 'none';
            cursorTrail.style.display = 'none';
        });
        
        document.addEventListener('mouseenter', function() {
            cursorDot.style.display = 'block';
            cursorTrail.style.display = 'block';
        });
        
        // Add click effect
        document.addEventListener('mousedown', function() {
            cursorDot.style.transform = 'translate(-50%, -50%) scale(0.8)';
            cursorTrail.style.transform = 'translate(-50%, -50%) scale(0.8)';
        });
        
        document.addEventListener('mouseup', function() {
            cursorDot.style.transform = 'translate(-50%, -50%) scale(1)';
            cursorTrail.style.transform = 'translate(-50%, -50%) scale(1)';
        });
    }
    
    // Initialize robot functionality
    function initRobotFunctionality() {
        // Get robot elements each time to ensure we have the latest DOM
        const robot = document.getElementById('robot');
        const leftEye = document.getElementById('left-eye');
        const rightEye = document.getElementById('right-eye');
        const mouth = document.querySelector('.mouth');
        
        if (!robot || !leftEye || !rightEye || !mouth) {
            // Try again in a bit if elements aren't available yet
            console.log("Robot elements not found, retrying...");
            setTimeout(initRobotFunctionality, 300);
            return;
        }
        
        console.log("Robot eye tracking initialized");
        
        // Remove any existing event listeners first (to avoid duplicates)
        document.removeEventListener('mousemove', trackEyes);
        
        // Create a named tracking function to be able to remove it later
        function trackEyes(e) {
            const mouseX = e.clientX;
            const mouseY = e.clientY;
            
            // Get position of each eye
            const leftRect = leftEye.getBoundingClientRect();
            const rightRect = rightEye.getBoundingClientRect();
            
            // Calculate the center of each eye
            const leftCenterX = leftRect.left + leftRect.width / 2;
            const leftCenterY = leftRect.top + leftRect.height / 2;
            const rightCenterX = rightRect.left + rightRect.width / 2;
            const rightCenterY = rightRect.top + rightRect.height / 2;
            
            // Calculate angle between mouse and eye
            const leftAngleRad = Math.atan2(mouseY - leftCenterY, mouseX - leftCenterX);
            const rightAngleRad = Math.atan2(mouseY - rightCenterY, mouseX - rightCenterX);
            
            // Limited movement distance for pupil
            const maxMovement = 1;
            
            // Move the pupils based on the angle
            const leftX = Math.cos(leftAngleRad) * maxMovement;
            const leftY = Math.sin(leftAngleRad) * maxMovement;
            const rightX = Math.cos(rightAngleRad) * maxMovement;
            const rightY = Math.sin(rightAngleRad) * maxMovement;
            
            leftEye.style.transform = `translate(${leftX}px, ${leftY}px)`;
            rightEye.style.transform = `translate(${rightX}px, ${rightY}px)`;
        }
        
        // Add the named function as event listener
        document.addEventListener('mousemove', trackEyes);
        
        // Handle hovering over navbar links - mouth opens
        const navLinks = document.querySelectorAll('.navbar a');
        navLinks.forEach(link => {
            link.addEventListener('mouseenter', () => {
                mouth.style.height = '6px';
                mouth.style.bottom = '25%';
            });
            
            link.addEventListener('mouseleave', () => {
                mouth.style.height = '2px';
                mouth.style.bottom = '30%';
            });
        });
        
        // Handle hovering over robot - robot smiles
        robot.addEventListener('mouseenter', () => {
            mouth.style.height = '2px';
            mouth.style.width = '60%';
            mouth.style.borderRadius = '0 0 90px 90px';
            mouth.style.bottom = '25%';
        });
        
        robot.addEventListener('mouseleave', () => {
            mouth.style.width = '40%';
            mouth.style.height = '2px';
            mouth.style.borderRadius = '0';
            mouth.style.bottom = '30%';
        });
    }
    
    // Enhanced cleanup function to ensure ALL styling is removed
    function removeSandboxStyling() {
        document.body.classList.remove('sandbox-active');
        
        // Reset navbar styling explicitly
        const navbarElements = document.querySelectorAll('.navbar, .navbar a');
        navbarElements.forEach(el => {
            el.style.fontFamily = '';
            el.style.textShadow = 'none';
            el.style.letterSpacing = '';
        });
        
        // Reset page title
        const pageTitle = document.getElementById('page-title');
        if (pageTitle) {
            pageTitle.style.fontFamily = '';
            pageTitle.style.color = '';
            pageTitle.style.textShadow = 'none';
            pageTitle.style.letterSpacing = '';
        }
        
        // Hide cursor elements
        const cursorElements = document.querySelectorAll('.cursor-dot, .cursor-trail');
        cursorElements.forEach(el => {
            el.style.display = 'none';
        });
        
        // Remove pixel effects
        const pixels = document.querySelectorAll('.retro-pixel');
        pixels.forEach(pixel => {
            if (pixel.parentNode) {
                pixel.parentNode.removeChild(pixel);
            }
        });
        
        // Force cursor back to default
        document.body.style.cursor = '';
    }
    ''')
    
], className="container retro-container", style={'minHeight': '100vh', 'paddingTop': '20px', 'paddingBottom': '20px', 'position': 'relative'})

# Toggle between games based on dropdown selection
@callback(
    Output('reaction-game-container', 'style'),
    Output('accuracy-game-container', 'style'),
    Input('game-selector', 'value')
)
def toggle_games(selected_game):
    if selected_game == 'reaction':
        return retro_styles['game_container'], {**retro_styles['game_container'], 'display': 'none'}
    else:
        return {**retro_styles['game_container'], 'display': 'none'}, retro_styles['game_container']

# Reaction Time Game Callbacks
@callback(
    Output('reaction-interval', 'disabled'),
    Output('reaction-state', 'data'),
    Output('reaction-box', 'style'),
    Output('start-reaction-test', 'disabled'),
    Input('start-reaction-test', 'n_clicks'),
    Input('reaction-interval', 'n_intervals'),
    Input('reaction-box', 'n_clicks'),
    State('reaction-state', 'data'),
    prevent_initial_call=True
)
def manage_reaction_game(start_clicks, intervals, box_clicks, state):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    base_style = {
        'width': '300px',
        'height': '300px',
        'borderRadius': '10px',
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
        'cursor': 'pointer',
        'margin': '0 auto',
        'position': 'relative',
        'boxShadow': '0 0 20px currentColor',
        'border': '4px solid currentColor',
        # Removed transition property for instant color change
    }
    
    if triggered_id == 'start-reaction-test' and state == 'idle':
        # User started the game
        # Minimum 0.5 seconds (5 intervals of 100ms) + random additional time
        wait_time = random.randint(5, 50)  # 0.5-5 seconds (in 100ms intervals)
        style = {**base_style, 'backgroundColor': '#08519c', 'boxShadow': '0 0 20px #08519c', 'border': '4px solid #08519c'}  # Blue
        return False, 'waiting', style, True
    
    elif triggered_id == 'reaction-interval' and state == 'waiting':
        intervals = intervals or 0
        if intervals >= 5 and intervals > random.randint(5, 50):  # Ensure minimum 0.5s wait
            # Change to green - time to click!
            style = {**base_style, 'backgroundColor': '#2ca02c', 'boxShadow': '0 0 20px #2ca02c', 'border': '4px solid #2ca02c'}  # Green
            return True, 'ready', style, True
        return False, 'waiting', {**base_style, 'backgroundColor': '#08519c', 'boxShadow': '0 0 20px #08519c', 'border': '4px solid #08519c'}, True
    
    elif triggered_id == 'reaction-box' and state == 'ready':
        # User clicked at the right time
        style = {**base_style, 'backgroundColor': '#08519c', 'boxShadow': '0 0 20px #08519c', 'border': '4px solid #08519c'}  # Back to blue
        return True, 'idle', style, False
    
    elif triggered_id == 'reaction-box' and state == 'waiting':
        # User clicked too early
        style = {**base_style, 'backgroundColor': '#d62728', 'boxShadow': '0 0 20px #d62728', 'border': '4px solid #d62728'}  # Red for error
        return True, 'idle', style, False
        
    # Default - no change
    return True, 'idle', {**base_style, 'backgroundColor': '#08519c', 'boxShadow': '0 0 20px #08519c', 'border': '4px solid #08519c'}, False

@callback(
    Output('reaction-start-time', 'data'),
    Input('reaction-state', 'data'),
    prevent_initial_call=True
)
def store_start_time(state):
    if state == 'ready':
        return time.time() * 1000  # Current time in milliseconds
    return None

@callback(
    Output('reaction-result', 'children'),
    Input('reaction-box', 'n_clicks'),
    State('reaction-state', 'data'),
    State('reaction-start-time', 'data'),
    prevent_initial_call=True
)
def show_reaction_result(clicks, state, start_time):
    if not clicks:
        raise PreventUpdate
    
    if state == 'ready' and start_time:
        reaction_time = time.time() * 1000 - start_time
        return [
            html.Div(f"YOUR REACTION TIME:", style={'marginTop': '20px'}),
            html.Div(f"{reaction_time:.1f} MS", style={'fontSize': '32px', 'fontWeight': 'bold', 'color': '#FFFF00'})
        ]
    elif state == 'waiting':
        return [
            html.Div("TOO EARLY!", style={'color': '#FF0000', 'fontSize': '24px'}),
            html.Div("TRY AGAIN", style={'marginTop': '10px'})
        ]
    return ""

# Cursor Accuracy Game Callbacks
@callback(
    Output('accuracy-state', 'data'),
    Output('accuracy-targets', 'data'),
    Output('accuracy-hits', 'data'),
    Output('accuracy-misses', 'data'),
    Output('accuracy-start-time', 'data'),
    Output('accuracy-box', 'children'),
    Output('start-accuracy-test', 'style'),  # New output to control button visibility
    Input('start-accuracy-test', 'n_clicks'),
    State('accuracy-state', 'data'),
    prevent_initial_call=True
)
def start_accuracy_game(clicks, state):
    if not clicks:
        raise PreventUpdate
    
    if state == 'idle':
        # Generate 10 random target positions - now across the entire box
        targets = []
        for i in range(10):
            targets.append({
                'id': f'target-{i}',
                'left': random.randint(20, 90),   # Percentage of width
                'top': random.randint(10, 90),    # Percentage of height
                'size': random.randint(20, 50)    # Size between 20-50px
            })
        
        # Create the first target
        current_target = targets[0]
        target_element = html.Div(
            id={'type': 'target', 'index': 0},
            style={
                'position': 'absolute',
                'left': f"{current_target['left']}%",
                'top': f"{current_target['top']}%",
                'width': f"{current_target['size']}px",
                'height': f"{current_target['size']}px",
                'backgroundColor': 'red',
                'borderRadius': '50%',
                'cursor': 'pointer',
                'boxShadow': '0 0 20px red',
                'border': '2px solid white',
                'zIndex': '10'
            }
        )
        
        # Hide the button during gameplay
        hidden_style = {**retro_styles['button'], 'display': 'none'}
        
        return 'playing', targets, 0, 0, time.time() * 1000, [target_element], hidden_style
    
    return 'idle', [], 0, 0, None, [], retro_styles['button']

@callback(
    Output('accuracy-box', 'children', allow_duplicate=True),
    Output('accuracy-hits', 'data', allow_duplicate=True),
    Output('accuracy-state', 'data', allow_duplicate=True),
    Output('start-accuracy-test', 'style', allow_duplicate=True),  # New output to control button visibility when game ends
    Input({'type': 'target', 'index': dash.ALL}, 'n_clicks'),
    State('accuracy-targets', 'data'),
    State('accuracy-hits', 'data'),
    prevent_initial_call=True
)
def handle_target_click(clicks, targets, hits):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    # Extract the index from the clicked target
    try:
        clicked_index = int(ctx.triggered[0]['prop_id'].split(',')[0].split(':')[1].rstrip('}'))
    except:
        raise PreventUpdate
    
    new_hits = hits + 1
    
    # Check if we've reached the end of the game
    if new_hits >= len(targets):
        # Show the button again when game is complete
        return [], new_hits, 'idle', retro_styles['button']
    
    # Otherwise, display the next target
    current_target = targets[new_hits]
    target_element = html.Div(
        id={'type': 'target', 'index': new_hits},
        style={
            'position': 'absolute',
            'left': f"{current_target['left']}%",
            'top': f"{current_target['top']}%",
            'width': f"{current_target['size']}px",
            'height': f"{current_target['size']}px",
            'backgroundColor': 'red',
            'borderRadius': '50%',
            'cursor': 'pointer',
            'boxShadow': '0 0 20px red',
            'border': '2px solid white',
            'zIndex': '10'
        }
    )
    
    # Keep the button hidden during gameplay
    hidden_style = {**retro_styles['button'], 'display': 'none'}
    
    return [target_element], new_hits, 'playing', hidden_style

@callback(
    Output('accuracy-result', 'children'),
    Input('accuracy-state', 'data'),
    Input('accuracy-hits', 'data'),
    Input('accuracy-start-time', 'data'),
    prevent_initial_call=True
)
def show_accuracy_result(state, hits, start_time):
    if state == 'idle' and hits > 0 and start_time:
        total_time = time.time() * 1000 - start_time
        avg_time = total_time / hits if hits > 0 else 0
        return [
            html.Div("GAME COMPLETE!", style={'fontSize': '24px', 'color': '#00FF00', 'marginTop': '20px'}),
            html.Div([
                html.Span("TARGETS HIT: ", style={'color': '#FFFFFF'}),
                html.Span(f"{hits}/10", style={'color': '#FFFF00'})
            ]),
            html.Div([
                html.Span("TOTAL TIME: ", style={'color': '#FFFFFF'}),
                html.Span(f"{total_time/1000:.1f} SEC", style={'color': '#FFFF00'})
            ]),
            html.Div([
                html.Span("AVG TARGET TIME: ", style={'color': '#FFFFFF'}),
                html.Span(f"{avg_time:.1f} MS", style={'color': '#FFFF00'})
            ])
        ]
    return ""