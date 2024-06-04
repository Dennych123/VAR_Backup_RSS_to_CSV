import struct
import lxml.etree as et
import pandas as pd
import ctypes


class SysmacData:
    def __init__(self, file_name):
        self.file_name = file_name
    @staticmethod
    def float_to_hex(float_value):
    # Determine precision (32-bit or 64-bit) based on the size of the float
        is_double_precision = (struct.calcsize("P") == 8)
    
    # Select format string based on precision
        if is_double_precision:
            fmt = '<d'  # '>d' for double precision (64-bit)
        else:
            fmt = '<f'  # '>f' for single precision (32-bit)
    
    # Pack float value into bytes in big endian format
        binary_data = struct.pack(fmt, float_value)
    
    # Convert binary data to hexadecimal string
        hex_data = binary_data.hex().upper()  # Convert to uppercase for consistency
    
        return hex_data

    
    @staticmethod
    def real_to_hex(real_number):
        binary_data = struct.pack('f', real_number)
        hex_data = binary_data.hex()
        return hex_data

    @staticmethod
    def hex_string_to_hex_number(hex_string):
        hex_number = int(hex_string, 16)
        return hex_number
    
    
    @staticmethod
    def int_to_bytes(integer_value, byte_order='big', signed=False):
        # Determine the number of bytes required to represent the integer
        num_bytes = (integer_value.bit_length() + 7) // 8
    
        # Convert the integer to bytes
        byte_data = integer_value.to_bytes(num_bytes, byte_order, signed=signed)
    
        return byte_data
    def parse_xml(self):
        xml_data = et.parse(f'{self.file_name}.xml')
        data_root = xml_data.find('Body')
        ret_vars = data_root.find('RetainVariable')

        lst_tag = []
        lst_data = []
        lst_type = []

        for item in ret_vars:
            tag = item.items()[0][1][6:]
            data_type = item.items()[1][1]
            data = item.find('Data')
            data_text = data.text

            if ('REAL' in data_type) or ('real' in data_type):
                lst_tag.append(tag)
                
                hex_numb=self.hex_string_to_hex_number(data_text)
                
                if 'LR' in data_type or 'lr' in data_type:
                    byte_data = self.int_to_bytes(hex_numb, byte_order='big', signed=False)
                    byte_data = byte_data.rjust(8, b'\x00')  # Pad with zeros to ensure 8 bytes
                    float_numb = struct.unpack('d', byte_data)[0]
                else:  # Single precision    
                    byte_data = self.int_to_bytes(hex_numb, byte_order='big', signed=False)[:4]
                    byte_data = byte_data.ljust(4, b'\x00')  # Pad with zeros to ensure 4 bytes
                    float_numb = struct.unpack('f', byte_data)[0]

                lst_data.append(float_numb)
                lst_type.append(data_type)
            elif ('STRING' in data_type) or ('string' in data_type):
                lst_tag.append(tag)
                if data_text is not None:
                    lst_data.append(bytearray.fromhex(data_text).decode())
                else:
                    lst_data.append('')
                lst_type.append(data_type)
            else:
                lst_tag.append(tag)
                lst_data.append(data.text)
                lst_type.append(data_type)

        data_dict = {'Tag': lst_tag, 'Data': lst_data, 'Type': lst_type}
        return data_dict

    def save_to_csv(self):
        data_dict = self.parse_xml()
        df = pd.DataFrame(data_dict)
        df.to_csv(f'{self.file_name}.csv', index=False)

    def csv_to_xml(self):
        df = pd.read_csv(f'{self.file_name}.csv')

        # Create the root element
        root = et.Element("Root")

        # Create the body element
        body = et.SubElement(root, "Body")

        # Create the RetainVariable element
        retain_vars = et.SubElement(body, "RetainVariable")

        # Iterate through the dataframe rows and build XML elements
        for index, row in df.iterrows():
            item = et.SubElement(retain_vars, "Item", Name=f"%s" % row["Tag"], Type=row["Type"])
            data = et.SubElement(item, "Data")

            if "REAL" in row["Type"] or "real" in row["Type"]:
                
                
                aas=float(row["Data"])
                saa=self.float_to_hex(aas)
                data.text = saa
                
            elif "STRING" in row["Type"] or "string" in row["Type"]:
                data_value = row["Data"]
                if isinstance(data_value, str):
                    data.text = bytearray(data_value, 'utf-8').hex()
                else:
                    data.text = ''
            else:
                data.text = str(row["Data"])

        # Generate the XML string with lxml.etree.tostring and include the XML declaration
        xml_string = et.tostring(root, encoding='utf-8', pretty_print=True, xml_declaration=True).decode('utf-8')

        # Save the XML string to a file
        with open(f'{self.file_name}_new_file.xml', 'w', encoding='utf-8') as xml_file:
            xml_file.write(xml_string)


if __name__ == '__main__':
    file_name = r'examples\controller_1__XY_RI90_01_CT90_03_042122'
    sysmac_data = SysmacData(file_name)
    sysmac_data.save_to_csv()
    sysmac_data.csv_to_xml()
