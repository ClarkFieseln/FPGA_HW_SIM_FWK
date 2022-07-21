
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
library hw_sim_fwk;
--mm use hw_sim_fwk.hw_sim_fwk_common.all;

-- Note: the followig metacomment is not part of the VHDL synthesis standard (IEEE P1076.6) so behavior is tool dependent.
-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_clock is
    generic(
        FILE_PATH                 : string  := "/tmp/";
        CLOCK_FILE_NAME           : string  := "/tmp/hw_sim_fwk/clock"; -- FILE_PATH & "clock_high" -- cannot use concatenation here!
        CLOCK_PERIOD              : time    := 20 ns;
        PROTOCOL_CLOCK            : boolean := false -- to report details
    );
    port(
        hw_clock : out std_logic
    );
end hw_sim_fwk_clock;

architecture arch of hw_sim_fwk_clock is
begin
    -- process to read FIFO
    -- ####################
    proc_update_clock : process
        file     i_file      : text;
        variable open_status : file_open_status;
        variable i_line      : line;
        -- NOTE: the variable "stimulus" could mean clock_level or edge_transition, but it does not matter
        --       because to keep things consistent we check in addition against the variable "pos_edge".
        variable stimulus   : std_logic;
        variable pos_edge            : boolean := false;
        variable initialized         : boolean := false;
    begin
        -- initialization?
        if initialized = false then
            initialized := true;
            -- open stimulus file
            loop
                file_open(open_status, i_file, CLOCK_FILE_NAME,  read_mode);
                exit when open_status = open_ok;
            end loop;
            -- "block" until new line is sent (no CPU consumption!)
            -------------------------------------------------------
            readline(i_file, i_line);
            read(i_line, stimulus);
            -- initialize hw_clock with external clock signal
            if stimulus = '1' then
                hw_clock <= '1';
                pos_edge := true;
                -- if (PROTOCOL_CLOCK = true) then
                report "hw_clock initialized to 1";
                -- end if;
            else
                hw_clock <= '0';
                pos_edge := false;
                -- if (PROTOCOL_CLOCK = true) then
                report "hw_clock initialized to 0";
                -- end if;
            end if;
        -- check external clock signal
        else
            -- with this loop we avoid re-checking the variable "initialized" unnecessarily            
            loop
                -- "block" until a new line is sent in fifo (named pipe)
                -------------------------------------------------------
                readline(i_file, i_line);
                read(i_line, stimulus);
                if (PROTOCOL_CLOCK = true) then
                    report "checking external clock..";
                end if;
                -- evaluate external clock signal
                if stimulus = '1' then
                
                    -- as a result of an error, the external clock signal may repeat the same edge transition
                    -- therefore we always check current state of pos_edge
                    -- rising edge?
                    if pos_edge = false then
                        pos_edge       := true;
                        hw_clock       <= '1';
                        wait for CLOCK_PERIOD / 2;
                    end if;
                -- stimulus /= '1':
                else
                    -- falling edge?
                    if pos_edge = true then
                        pos_edge := false;
                        hw_clock <= '0';
                        wait for CLOCK_PERIOD / 2;
                    end if;
                end if;
            end loop;
            -- TODO: implement condition (e.g. special value in clock stimulus) to get here..
            --       and add another flag (?) to get out of the process (?)
            -- file_close(i_file);
            -- report "Left process proc_update_clock in hw_sim_fwk_clock"; -- severity note;
        end if;
    end process proc_update_clock;
end arch;

-- synthesis translate_on
-- ######################
