# -*- coding: utf-8 -*-
"""streamlit_app.ipynb

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="ODE Solver", layout="centered", page_icon="📈")
st.title("📈 ODE Solver: Widely-Used Numerical Methods")

st.sidebar.header("Instructions & Input Format")
st.sidebar.markdown("""
- **Express your ODE (any order) as a system of first-order ODEs.**
    - For nth-order ODE, define:
      x₀ = y, x₁ = y', x₂ = y'', ..., xₙ₋₁ = y⁽ⁿ⁻¹⁾
    - Example for y'' = -y:
      `lambda t, X: [X[1], -X[0]]`
- **Initial conditions:** comma-separated, e.g. `1, 0` for y(0)=1, y'(0)=0
""")

methods = [
    "Euler's Method",
    "Runge-Kutta 2nd Order",
    "Runge-Kutta 4th Order",
    "Runge-Kutta-Fehlberg (RKF45, Adaptive)",
    "Adams-Bashforth (Explicit, 4th Order)",
    "Adams-Moulton (Implicit, 4th Order)",
    "Backward Differentiation Formula (BDF, 2nd Order)",
    "Verlet (for 2nd-order ODEs)",
    "Symplectic (Stormer-Verlet, for Hamiltonian systems)"
]
method = st.sidebar.selectbox("Select Numerical Method", methods)

ode_input = st.sidebar.text_area(
    "Enter ODE system as a lambda function:",
    value="lambda t, X: [X[1], -X[0]]",
    height=120,
    help="Return list of derivatives: [x0', x1', ..., xn']"
)
y0_str = st.sidebar.text_input(
    "Initial conditions (comma-separated):",
    value="1, 0",
    help="Initial values for all state variables at t₀"
)
t0 = st.sidebar.number_input("Initial time (t₀)", value=0.0)
t_final = st.sidebar.number_input("Final time", value=10.0, min_value=t0 + 1e-6)
h = st.sidebar.number_input("Step size (h)", value=0.1, min_value=1e-6, max_value=5.0)

# Parse inputs
try:
    y0 = [float(x.strip()) for x in y0_str.split(",")]
    n = len(y0)
except Exception:
    st.error("❌ Invalid initial conditions. Use comma-separated numbers.")
    st.stop()

try:
    f = eval(ode_input)
    test_output = f(0, np.zeros(n))
    if len(test_output) != n:
        st.error(f"❌ ODE function must return {n} derivatives (got {len(test_output)})")
        st.stop()
except Exception as e:
    st.error(f"❌ Invalid ODE function: {str(e)}")
    st.stop()

n_steps = int(np.ceil((t_final - t0) / h))
if n_steps <= 0:
    st.error("❌ Invalid time interval or step size")
    st.stop()

# ====== NUMERICAL METHODS ======
def euler(f, t0, y0, h, n_steps):
    t = np.zeros(n_steps + 1)
    Y = np.zeros((n_steps + 1, len(y0)))
    t[0], Y[0] = t0, y0
    for i in range(n_steps):
        Y[i+1] = Y[i] + h * np.array(f(t[i], Y[i]))
        t[i+1] = t[i] + h
    return t, Y

def rk2(f, t0, y0, h, n_steps):
    t = np.zeros(n_steps + 1)
    Y = np.zeros((n_steps + 1, len(y0)))
    t[0], Y[0] = t0, y0
    for i in range(n_steps):
        k1 = np.array(f(t[i], Y[i]))
        k2 = np.array(f(t[i] + h/2, Y[i] + (h/2)*k1))
        Y[i+1] = Y[i] + h * k2
        t[i+1] = t[i] + h
    return t, Y

def rk4(f, t0, y0, h, n_steps):
    t = np.zeros(n_steps + 1)
    Y = np.zeros((n_steps + 1, len(y0)))
    t[0], Y[0] = t0, y0
    for i in range(n_steps):
        k1 = np.array(f(t[i], Y[i]))
        k2 = np.array(f(t[i] + h/2, Y[i] + (h/2)*k1))
        k3 = np.array(f(t[i] + h/2, Y[i] + (h/2)*k2))
        k4 = np.array(f(t[i] + h, Y[i] + h*k3))
        Y[i+1] = Y[i] + (h/6)*(k1 + 2*k2 + 2*k3 + k4)
        t[i+1] = t[i] + h
    return t, Y

def rkf45(f, t0, y0, t_final, h_init=0.1, tol=1e-5):
    t = [t0]
    Y = [np.array(y0)]
    h = h_init
    while t[-1] < t_final:
        ti, yi = t[-1], Y[-1]
        if ti + h > t_final:
            h = t_final - ti
        k1 = np.array(f(ti, yi))
        k2 = np.array(f(ti + h/4, yi + h*k1/4))
        k3 = np.array(f(ti + 3*h/8, yi + h*(3*k1/32 + 9*k2/32)))
        k4 = np.array(f(ti + 12*h/13, yi + h*(1932*k1/2197 - 7200*k2/2197 + 7296*k3/2197)))
        k5 = np.array(f(ti + h, yi + h*(439*k1/216 - 8*k2 + 3680*k3/513 - 845*k4/4104)))
        k6 = np.array(f(ti + h/2, yi + h*(-8*k1/27 + 2*k2 - 3544*k3/2565 + 1859*k4/4104 - 11*k5/40)))
        y4 = yi + h*(25*k1/216 + 1408*k3/2565 + 2197*k4/4104 - k5/5)
        y5 = yi + h*(16*k1/135 + 6656*k3/12825 + 28561*k4/56430 - 9*k5/50 + 2*k6/55)
        err = np.linalg.norm(y5 - y4)
        if err < tol:
            t.append(ti + h)
            Y.append(y5)
            h *= min(2, (tol/err)**0.25) if err > 0 else 2
        else:
            h *= max(0.1, 0.9*(tol/err)**0.25)
    return np.array(t), np.array(Y)

def adams_bashforth(f, t0, y0, h, n_steps):
    t = np.zeros(n_steps + 1)
    Y = np.zeros((n_steps + 1, len(y0)))
    t[0], Y[0] = t0, y0
    for i in range(3):
        if i >= n_steps:
            break
        k1 = np.array(f(t[i], Y[i]))
        k2 = np.array(f(t[i] + h/2, Y[i] + (h/2)*k1))
        k3 = np.array(f(t[i] + h/2, Y[i] + (h/2)*k2))
        k4 = np.array(f(t[i] + h, Y[i] + h*k3))
        Y[i+1] = Y[i] + (h/6)*(k1 + 2*k2 + 2*k3 + k4)
        t[i+1] = t[i] + h
    for i in range(3, n_steps):
        f1 = np.array(f(t[i], Y[i]))
        f2 = np.array(f(t[i-1], Y[i-1]))
        f3 = np.array(f(t[i-2], Y[i-2]))
        f4 = np.array(f(t[i-3], Y[i-3]))
        Y[i+1] = Y[i] + h/24*(55*f1 - 59*f2 + 37*f3 - 9*f4)
        t[i+1] = t[i] + h
    return t, Y

def adams_moulton(f, t0, y0, h, n_steps):
    t = np.zeros(n_steps + 1)
    Y = np.zeros((n_steps + 1, len(y0)))
    t[0], Y[0] = t0, y0
    for i in range(3):
        if i >= n_steps:
            break
        k1 = np.array(f(t[i], Y[i]))
        k2 = np.array(f(t[i] + h/2, Y[i] + (h/2)*k1))
        k3 = np.array(f(t[i] + h/2, Y[i] + (h/2)*k2))
        k4 = np.array(f(t[i] + h, Y[i] + h*k3))
        Y[i+1] = Y[i] + (h/6)*(k1 + 2*k2 + 2*k3 + k4)
        t[i+1] = t[i] + h
    for i in range(3, n_steps):
        f1 = np.array(f(t[i], Y[i]))
        f2 = np.array(f(t[i-1], Y[i-1]))
        f3 = np.array(f(t[i-2], Y[i-2]))
        f4 = np.array(f(t[i-3], Y[i-3]))
        y_pred = Y[i] + h/24*(55*f1 - 59*f2 + 37*f3 - 9*f4)
        f_pred = np.array(f(t[i] + h, y_pred))
        Y[i+1] = Y[i] + h/24*(9*f_pred + 19*f1 - 5*f2 + f3)
        t[i+1] = t[i] + h
    return t, Y

def bdf2(f, t0, y0, h, n_steps):
    t = np.zeros(n_steps + 1)
    Y = np.zeros((n_steps + 1, len(y0)))
    t[0], Y[0] = t0, y0
    if n_steps > 0:
        Y[1] = Y[0] + h * np.array(f(t[0], Y[0]))
        t[1] = t[0] + h
    for i in range(1, n_steps):
        y_guess = Y[i]
        for _ in range(3):
            y_guess = (4*Y[i] - Y[i-1] + 2*h*np.array(f(t[i] + h, y_guess))) / 3
        Y[i+1] = y_guess
        t[i+1] = t[i] + h
    return t, Y

def verlet(f, t0, y0, h, n_steps):
    t = np.zeros(n_steps + 1)
    Y = np.zeros((n_steps + 1, 2))
    t[0], Y[0] = t0, y0
    a0 = f(t[0], Y[0, 0])
    Y[1, 1] = Y[0, 1] + 0.5*h*a0
    Y[1, 0] = Y[0, 0] + h*Y[1, 1]
    t[1] = t[0] + h
    for i in range(1, n_steps):
        a_i = f(t[i], Y[i, 0])
        Y[i+1, 1] = Y[i, 1] + h*a_i
        Y[i+1, 0] = Y[i, 0] + h*Y[i+1, 1]
        t[i+1] = t[i] + h
    return t, Y

def stormer_verlet(f, t0, y0, h, n_steps):
    t = np.zeros(n_steps + 1)
    Y = np.zeros((n_steps + 1, 2))
    t[0], Y[0] = t0, y0
    for i in range(n_steps):
        p_half = Y[i, 1] + 0.5*h*f(t[i], Y[i, 0])
        q_next = Y[i, 0] + h*p_half
        p_next = p_half + 0.5*h*f(t[i] + h, q_next)
        Y[i+1, 0] = q_next
        Y[i+1, 1] = p_next
        t[i+1] = t[i] + h
    return t, Y

# ====== DISPATCH SOLVER ======
if method == "Euler's Method":
    t, Y = euler(f, t0, y0, h, n_steps)
elif method == "Runge-Kutta 2nd Order":
    t, Y = rk2(f, t0, y0, h, n_steps)
elif method == "Runge-Kutta 4th Order":
    t, Y = rk4(f, t0, y0, h, n_steps)
elif method == "Runge-Kutta-Fehlberg (RKF45, Adaptive)":
    t, Y = rkf45(f, t0, y0, t_final, h_init=h)
elif method == "Adams-Bashforth (Explicit, 4th Order)":
    t, Y = adams_bashforth(f, t0, y0, h, n_steps)
elif method == "Adams-Moulton (Implicit, 4th Order)":
    t, Y = adams_moulton(f, t0, y0, h, n_steps)
elif method == "Backward Differentiation Formula (BDF, 2nd Order)":
    t, Y = bdf2(f, t0, y0, h, n_steps)
elif method == "Verlet (for 2nd-order ODEs)":
    def accel(t, y):
        state = np.array([y, 0])
        return f(t, state)[1]
    t, Y = verlet(accel, t0, np.array(y0), h, n_steps)
elif method == "Symplectic (Stormer-Verlet, for Hamiltonian systems)":
    def force(t, q):
        state = np.array([q, 0])
        return f(t, state)[1]
    t, Y = stormer_verlet(force, t0, np.array(y0), h, n_steps)

# ====== VISUALIZATION ======
st.subheader("Solution Visualization")
fig, ax = plt.subplots(figsize=(8, 6))
for i in range(Y.shape[1]):
    ax.plot(t, Y[:, i], label=f"$x_{i}(t)$")
ax.set_xlabel("Time (t)")
ax.set_ylabel("State Variables")
ax.set_title(f"Solution using {method}")
ax.legend()
ax.grid(True)
st.pyplot(fig)

if Y.shape[1] >= 2:
    st.subheader("Phase Space Plot")
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    ax2.plot(Y[:, 0], Y[:, 1], color='purple')
    ax2.scatter(Y[0, 0], Y[0, 1], color='red', label='Start', s=100)
    ax2.scatter(Y[-1, 0], Y[-1, 1], color='blue', label='End', s=100)
    ax2.set_xlabel("$x_0$")
    ax2.set_ylabel("$x_1$")
    ax2.set_title("Phase Portrait")
    ax2.legend()
    ax2.grid(True)
    st.pyplot(fig2)

st.subheader("Numerical Results")
df = pd.DataFrame(Y, columns=[f"x_{i}" for i in range(Y.shape[1])])
df.insert(0, "Time", t)
st.dataframe(df.style.format("{:.6f}"), height=300)

st.subheader("Numerical Methods Comparison")
st.markdown("""
| Method                           | Order | Stability      | Famous Applications                                   |
|----------------------------------|-------|----------------|------------------------------------------------------|
| Euler's Method                   | 1     | Conditional    | Education, simple simulations                        |
| Runge-Kutta 2nd Order            | 2     | Conditional    | Real-time systems, game physics                      |
| Runge-Kutta 4th Order            | 4     | Conditional    | Engineering, aerospace, robotics                     |
| RKF45 (Adaptive)                 | 4-5   | Adaptive       | Aerospace, scientific computing                      |
| Adams-Bashforth (Explicit)       | 2-6   | Conditional    | Climate modeling, fluid dynamics                     |
| Adams-Moulton (Implicit)         | 2-6   | Unconditional  | Circuit simulation, control systems                  |
| BDF (Implicit)                   | 1-6   | Very stable    | Chemical kinetics, stiff systems                     |
| Verlet                           | 2     | Energy-pres.   | Molecular dynamics, astrophysics                     |
| Stormer-Verlet (Symplectic)      | 2     | Structure-pres.| Quantum mechanics, celestial mechanics               |
""")

