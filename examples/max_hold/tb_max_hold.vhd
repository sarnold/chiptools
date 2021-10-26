-------------------------------------------------------------------------------
-- tb_max_hold.vhd
-- This testbench instances the max_hold component and exercises it with data
-- from the input.txt stimulus file. The input.txt stimulus file should contain
-- the following data on each line:
-- <RESET (1bit)> <DATA (nbit)>
-- The output file format is simply rows of binary data where each row contains
-- an nbit binary value.
-------------------------------------------------------------------------------

library ieee;
    use ieee.std_logic_1164.all;
    use ieee.numeric_std.all;
    use ieee.math_real.all;

library std;
    use std.textio.all;

library lib_max_hold;
    use lib_max_hold.pkg_max_hold.all;

entity tb_max_hold is
    generic (
        data_width : positive := 12
    );
end entity;

architecture beh of tb_max_hold is
    signal uut_data     : std_logic_vector(data_width-1 downto 0)
        := (others => '0');
    signal uut_output   : std_logic_vector(data_width-1 downto 0);
    signal clock        : std_logic := '0';
    signal reset        : std_logic := '0';
    signal done         : boolean := false;
begin
    -- Test source clock
    clockgen : process(clock)
    begin
        if not done then
            clock <= not clock after 10 ns;
        end if;
    end process;
    -- Simple process to read and write the stimulus files.
    stim_parser : process
        constant input_path     : string := "input.txt";
        constant output_path    : string := "output.txt";
        file     input_file     : text;
        file     output_file    : text;
        variable data_line      : line;
        variable output_line    : line;
        variable status         : file_open_status := status_error;
        variable in_reset       : bit_vector(0 downto 0);
        variable data           : bit_vector(data_width-1 downto 0);
        variable read_ok        : boolean;
        variable first_call     : boolean := true;
    begin
        if status /= open_ok then
            file_open(status, input_file, input_path, read_mode);
            assert (status = open_ok)
                report "Failed to open " & input_path
                severity failure;
            file_open(status, output_file, output_path, write_mode);
            assert (status = open_ok)
                report "Failed to open " & output_path
                severity failure;
        end if;

        if not endfile(input_file) then
            readline(input_file, data_line);
            -- Get Reset
            read(data_line, in_reset, read_ok);
            reset <= to_stdlogicvector(in_reset)(0);
            -- Get Data
            read(data_line, data, read_ok);
            uut_data <= to_stdlogicvector(data);
            wait until rising_edge(clock);
            if first_call then
                first_call := false;
            else
                -- Record current maximum
                write(output_line, to_bitvector(uut_output));
                writeline(output_file, output_line);
            end if;
        else
            wait until rising_edge(clock);
            -- Record current maximum
            write(output_line, to_bitvector(uut_output));
            writeline(output_file, output_line);
            -- Simulation Finished
            done <= true;
            wait;
        end if;
    end process;
    -- UUT instance
    uut : entity lib_max_hold.max_hold
    generic map(
        data_width  => data_width
    )
    port map(
        clock       => clock,
        reset       => reset,
        data        => uut_data,
        max         => uut_output
    );
end beh;
