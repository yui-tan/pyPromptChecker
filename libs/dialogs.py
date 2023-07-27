def make_control_net_page(target, data):
    page_layout = QVBoxLayout()
    for key, value in data.items():
        if target in key and target != key:
            data_layout = QHBoxLayout()
            title = key.replace(target, '').strip()
            if title.lower() == 'model':
                value = value.replace(' [', '\n[')
            title = QLabel(title.capitalize())
            value = QLabel(value.capitalize())
            data_layout.addWidget(title)
            data_layout.addWidget(value)
            page_layout.addLayout(data_layout)
    return page_layout