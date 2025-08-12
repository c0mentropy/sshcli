class PrintTable:
    def __init__(self):
        self.total: int = 0
        self.column_widths: dict = {}
    
    def get_column_widths(self, data: list[dict]) -> dict:
        
        total = 0
        # column_widths = {}
        if len(data) > 0:
            for header in data[0]:
                self.column_widths[header] = len(header)
        
        for row in data:
            for key in row:
                self.column_widths[key] = max(self.column_widths[key], len(str(row[key])))
        
        # print(self.column_widths)
        total = sum(self.column_widths.values()) + int("4") * len(self.column_widths)
        # print(total)

        self.column_widths['Total'] = total
        self.total = total

        return self.column_widths

    # ╷  ╪ ═   │
    def printf(self, data: list[dict], title: str = ""):
        if len(self.column_widths) == 0:
            self.column_widths = self.get_column_widths(data)

        if title != "":

            title_space_length = (self.total - len(title)) // 2 - 1
            print(f"\n{' '*title_space_length}{title}\n")

        header = ''
        header_line = ''
        for key, value in self.column_widths.items():
            if key != 'Total':
                header += f" {key:<{value}} ╷ "
                header_line += '═'*(value + 2) + "╪" + '═'*1

        header.rstrip('  ')

        print(header)
        print(header_line)

        for row in data:
            row_data = ''
            for key, value in self.column_widths.items():
                if key != 'Total':
                    row_data += f" {row[key]:<{value}} │ "
            
            print("\033[4m" + row_data + "\033[0m")
        
        print()

if __name__ == '__main__':

    user_datas = {
        "hosts1": {"username": "u1", "password": "xxxxxxxxxxxxxxxxw1"},
        "hosts2": {"username": "xxxxxxxxxxxxu2", "password": "w2"},
        "hosts3": {"username": "u3", "password": "w3"},
        "xxxxxxxxxxxxxxxxxhosts4": {"username": "u4", "password": "w4"}
    }

    table_data = []
    idx = 1
    for host, user_data in user_datas.items():
        table = {}
        table['ID'] = idx
        table['User'] = user_data['username']
        table['Platform'] = 'linux'
        table['Type'] = 'ssh'
        table['Address'] = host

        table_data.append(table)

        idx += 1
    
    print_table = PrintTable()
    print_table.printf(table_data)