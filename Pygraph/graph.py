import numpy as np
import pyqtgraph as pg
from collections import defaultdict

# read data from file
ips = []
counts = []
total_packets = 0

with open("flowSpread1.txt") as f:
    for line in f:
        parts = line.split()
        if len(parts) < 2:
            continue
        ip, size = parts[0], int(parts[1])
        ips.append(ip)
        counts.append(size)
        total_packets += size

biggest_idx = counts.index(max(counts))
print("\nIP with most packets sent: " + ips[biggest_idx] + ": " + str(counts[biggest_idx]))
print("Total packets: " + str(total_packets))

# group ips by their packet count value
count_to_ips = defaultdict(list)
for ip, c in zip(ips, counts):
    count_to_ips[c].append(ip)

unique_counts = sorted(count_to_ips.keys())
ip_freq = [len(count_to_ips[c]) for c in unique_counts]

x = np.arange(len(unique_counts))
log_freq = np.log10(np.maximum(np.array(ip_freq, dtype=float), 1))

# axis that turns log values back into real ip counts
class LogTicksAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [f"{10**v:.0f}" for v in values]

# axis that shows the actual packet count at each bar position
class PacketCountAxis(pg.AxisItem):
    def __init__(self, unique_counts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unique_counts = unique_counts

    def tickStrings(self, values, scale, spacing):
        out = []
        for v in values:
            idx = int(round(v))
            out.append(str(self.unique_counts[idx]) if 0 <= idx < len(self.unique_counts) else "")
        return out

app = pg.mkQApp("Flow Spread")

win = pg.GraphicsLayoutWidget(title="IP Count per Packet-Count Value")
win.resize(1100, 650)

plot = win.addPlot(
    axisItems={
        'left': LogTicksAxis(orientation='left'),
        'bottom': PacketCountAxis(unique_counts, orientation='bottom')
    }
)
plot.setTitle(f"Number of IPs per Packet Count — {len(unique_counts)} unique values")
plot.setLabel('left', 'Number of IPs (log scale)')
plot.setLabel('bottom', 'Packets sent (least → greatest)')
plot.showGrid(x=False, y=True, alpha=0.3)

bars = pg.BarGraphItem(x=x, height=log_freq, width=0.9, brush=(70, 130, 180))
plot.addItem(bars)
plot.setXRange(-1, len(unique_counts))
plot.setYRange(0, log_freq.max() * 1.05)

# tooltip and guide line for hovering
tooltip = pg.TextItem(anchor=(0, 1), fill=(50, 50, 50, 200), color='w')
tooltip.hide()
plot.addItem(tooltip)

vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('y', width=1))
vLine.hide()
plot.addItem(vLine)

def on_mouse_moved(evt):
    pos = evt[0]
    if not plot.sceneBoundingRect().contains(pos):
        tooltip.hide()
        vLine.hide()
        return

    mouse_point = plot.vb.mapSceneToView(pos)
    idx = int(round(mouse_point.x()))
    if idx < 0 or idx >= len(unique_counts):
        tooltip.hide()
        vLine.hide()
        return

    packet_val = unique_counts[idx]
    matching_ips = count_to_ips[packet_val]
    n_ips = len(matching_ips)

    # if only one ip has this count just show its name
    # otherwise list a few examples
    if n_ips == 1:
        ip_text = matching_ips[0]
    else:
        ip_text = ", ".join(matching_ips[:3]) + ("..." if n_ips > 3 else "")

    tooltip.setText(f"{packet_val} packets\n{n_ips} IP(s)\n{ip_text}")
    tooltip.setPos(idx, log_freq[idx] + 0.05 * log_freq.max())
    tooltip.show()

    vLine.setPos(idx)
    vLine.show()

proxy = pg.SignalProxy(plot.scene().sigMouseMoved, rateLimit=60, slot=on_mouse_moved)

win.show()
pg.exec()