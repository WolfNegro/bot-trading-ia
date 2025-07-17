import subprocess

print(">>> Ejecutando el bot en tiempo real...")
subprocess.run(["python", "scripts/real_time_bot.py"])

print(">>> Generando gráfico de operaciones...")
subprocess.run(["python", "scripts/plot_trades.py"])

print(">>> Todo listo. Verifica el archivo output/trades_plot.png")
