from PIL import Image, ImageDraw, ImageFont

vu_navy = (0, 31, 91)
vu_blue = (80, 145, 205)
vu_orange = (248, 151, 40)

def comma(num):
    return '{:,}'.format(num)

def smart_text(draw, text, x, y, font):
    draw.text((x - 1, y), text, fill=vu_navy, font=font)
    draw.text((x, y - 1), text, fill=vu_navy, font=font)
    draw.text((x + 1, y), text, fill=vu_navy, font=font)
    draw.text((x, y + 1), text, fill=vu_navy, font=font)
    draw.text((x - 1, y + 1), text, fill=vu_navy, font=font)
    draw.text((x - 1, y - 1), text, fill=vu_navy, font=font)
    draw.text((x + 1, y + 1), text, fill=vu_navy, font=font)
    draw.text((x + 1, y - 1), text, fill=vu_navy, font=font)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)

def bar_graph(filename, data, title=None, key=None, labels=None, numbers=True):
    bar_width = 60
    bar_gap = 15
    bar_border = 1
    padding = 20
    width = ((bar_width + bar_gap) * len(data)) - bar_gap + padding * 2
    height = 600

    im = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    gotham_font = ImageFont.truetype("fonts/Gotham-Medium.otf", 10)

    bottom_pad = 0
    if labels != None:
        for l in labels:
            _, th = draw.textsize(l, font=gotham_font, spacing=2)
            if th > bottom_pad:
                bottom_pad = th
    bottom = height - (padding / 2) - bottom_pad
    colors = [vu_navy, vu_blue, vu_orange]

    x = padding
    max = 0
    for arr in data:
        for d in arr:
            if d > max:
                max = d
    bar = 0
    totals = []
    for i in data[0]:
        totals.append(0)
    for arr in data:
        arr.sort(reverse=True)
        index = 0
        for d in arr:
            totals[index] += d
            if d == 0:
                continue
            bar_h = (height - bottom_pad - padding * 2) * (d / max)
            if index == 0:
                box = (
                    x - bar_border,
                    bottom - bar_h - bar_border,
                    x + bar_width + bar_border,
                    bottom + bar_border
                )
                draw.rectangle(box, fill=(0, 0, 0))
                if numbers:
                    c_arr = []
                    c_colors = []
                    for i in range(len(arr)):
                        if arr[i] > 0:
                            c_arr.append(arr[i])
                            c_colors.append(colors[i])
                    stats = ", ".join([comma(d) for d in c_arr])
                    _, h = draw.textsize("0,", font=gotham_font)
                    w, _ = draw.textsize(stats, font=gotham_font)
                    for i in range(len(c_arr)):
                        stats = ", ".join([comma(d) for d in c_arr[i:]])
                        draw.text((x + bar_width + bar_border - w, bottom - bar_h - h), comma(c_arr[i]), fill=c_colors[i], spacing=2, font=gotham_font)
                        if i == len(c_arr) - 1:
                            break
                        sub_w, _ = draw.textsize(comma(c_arr[i]), font=gotham_font)
                        w -= sub_w
                        draw.text((x + bar_width + bar_border - w, bottom - bar_h - h), ", ", fill=c_colors[0], spacing=2, font=gotham_font)
                        sub_w, _ = draw.textsize(", ", font=gotham_font)
                        w -= sub_w
            box = (
                x,
                bottom - bar_h,
                x + bar_width,
                bottom
            )
            draw.rectangle(box, fill=(colors[index]))
            index += 1
        if labels != None:
            draw.text((x, bottom + 3), labels[bar], fill=(0, 0, 0), spacing=2, font=gotham_font)
        x += bar_width + bar_gap
        bar += 1

    # Titles
    if title != None:
        gotham_title = ImageFont.truetype("fonts/Gotham-Black.otf", 24)
        title_w, title_h = draw.textsize(title, font=gotham_title)
        draw.text((width - title_w - padding, padding), title, fill=(0, 0, 0), font=gotham_title)

    # Key
    if key != None:
        y = padding + 28
        max_w = 0
        max_h = 0
        for k in key:
            w, h = draw.textsize(k, font=gotham_font)
            if w > max_w:
                max_w = w
            if h > max_h:
                max_h = h
        for i in range(len(key)):
            # Bar
            draw.rectangle((width - max_w - padding - 20, y, width - padding, y + max_h + 9), fill=(colors[i]))
            smart_text(draw, key[i], width - max_w - padding - 10, y + 5, gotham_font)
            # Totals
            total_text = comma(totals[i])
            if i > 0:
                total_text += " (%.1f%%)" % (100 * totals[i] / totals[0])
            total_w, _ = draw.textsize(total_text, font=gotham_font)
            draw.text((width - total_w - max_w - padding - 25, y + 5), total_text, fill=(colors[i]), font=gotham_font)
            y += max_h + 9 + 5

    del draw
    im.save(filename)

def horizontal_graph(filename, data, title=None, key=None, labels=None, numbers=True):
    im = Image.new("RGB", (1, 1), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    gotham_font = ImageFont.truetype("fonts/Gotham-Medium.ttf", 10)
    gotham_title = ImageFont.truetype("fonts/Gotham-Black.ttf", 15)

    colors = [vu_navy, vu_blue, vu_orange]
    _, line_height = draw.textsize("0,", font=gotham_font)

    bar_width = line_height * len(data[0]["sections"][0])
    bar_gap = line_height * 3
    bar_border = 1
    padding = 20
    width = 800
    height = ((bar_width * len(data[0]["sections"]) + bar_gap) * len(data)) - bar_gap + (padding * 2) + 28 # room for keys - padding / 2

    im = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(im)

    left_pad = 0
    if "labels" in data[0]:
        for bar in data:
            tw, _ = draw.textsize(comma(bar["total"]), font=gotham_font, spacing=2)
            if tw > left_pad:
                left_pad = tw
    left_pad += padding

    totals = []
    for i in data[0]:
        totals.append(0)
    for bar in data:
        for section in bar["sections"]:
            i = 0
            for n in section:
                totals[i] += n
                i += 1

    # Key
    key_height = 1
    if key != None:
        y = padding / 2
        max_w = 0
        max_h = 0
        for k in key:
            w, h = draw.textsize(k, font=gotham_font)
            if w > max_w:
                max_w = w
            if h > max_h:
                max_h = h
        total_totals = 0
        for bar in data:
            total_totals += bar["total"]
        for i in range(len(key)):
            # Bar
            draw.rectangle((width - max_w - padding - 19, y, width - padding + 1, y + max_h + 10), fill=(colors[i + 1]))
            smart_text(draw, key[i], width - max_w - padding - 10, y + 5, gotham_font)
            # Totals
            total_text = comma(totals[i])
            total_text += " (%.1f%%)" % (100 * totals[i] / total_totals)
            total_w, _ = draw.textsize(total_text, font=gotham_font)
            draw.text((width - total_w - max_w - padding - 25, y + 5), total_text, fill=(colors[i + 1]), font=gotham_font)
            y += max_h + 9 + 5
            key_height += max_h + 9 + 5

    # BARS
    bar_y = padding + 35 # room for keys
    max = 0
    for bar in data:
        if bar["total"] > max:
            max = bar["total"]
    bar_index = 0
    for bar in data:
        # background bar
        box = (
            left_pad - bar_border,
            bar_y - bar_border,
            left_pad + ((width - left_pad - padding) * (bar["total"] / max)) + bar_border,
            bar_y + (bar_width * len(bar["sections"])) + bar_border,
        )
        draw.rectangle(box, fill=colors[0])
        if "title" in bar:
            draw.text((left_pad, bar_y - line_height - 6), bar["title"], fill=(0, 0, 0), spacing=2, font=gotham_bold)
        if numbers:
            tw, _ = draw.textsize(comma(bar["total"]), font=gotham_font)
            draw.text((left_pad - tw - padding / 2, bar_y - line_height + 1), comma(bar["total"]), fill=colors[0], spacing=2, font=gotham_font)
        # section bars
        index = 0
        for section in bar["sections"]:
            section.sort(reverse=True)
            section_color = 1
            for n in section:
                totals[section_color - 1] += n
                if n == 0:
                    continue
                bar_h = (width - left_pad - padding) * (n / max)
                box = (
                    left_pad,
                    bar_y,
                    left_pad + bar_h,
                    bar_y + bar_width,
                )
                draw.rectangle(box, fill=(colors[section_color]))
                section_color += 1
            if numbers:
                section.sort(reverse=False)
                text_y = bar_y
                i = 1
                for n in section:
                    w, _ = draw.textsize(comma(n), font=gotham_font)
                    draw.text((left_pad - w - padding / 2, text_y + 1), comma(n), fill=colors[len(colors) - i], spacing=2, font=gotham_font)
                    if bar_index == 0 and i == 1:
                        smart_text(draw, bar["labels"][index], left_pad + 2, text_y + 2, font=gotham_font)
                    text_y += line_height
                    i += 1
            bar_y += bar_width
            index += 1
        bar_y += bar_gap
        bar_index += 1

    # Titles
    if title != None:
        gotham_title = ImageFont.truetype("fonts/Gotham-Black.otf", 24)
        title_w, title_h = draw.textsize(title, font=gotham_title)
        draw.text((width - title_w - padding, padding), title, fill=(0, 0, 0), font=gotham_title)

    del draw
    im.save(filename)
