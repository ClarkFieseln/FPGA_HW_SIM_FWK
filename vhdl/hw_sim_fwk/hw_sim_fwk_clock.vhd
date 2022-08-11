
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
library hw_sim_fwk;


-- Note: the followig metacomment is not part of the VHDL synthesis standard (IEEE P1076.6) so behavior is tool dependent.
-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_clock is
    generic(
        FIFO_PATH                 : string  := "\\.\pipe\";
        CLOCK_FILE_NAME           : string  := FIFO_PATH & "clock_high";
        CLOCK_PERIOD              : time    := 20 ns;
        PROTOCOL_CLOCK            : boolean := false
    );
    port(
        hw_clock : out std_logic
    );
end hw_sim_fwk_clock;

architecture arch of hw_sim_fwk_clock is
begin
    -- clock reading process
    -- #####################
    proc_update_clock : process
        type CHARACTER_FILE is file of character;
        file     i_file      : CHARACTER_FILE;
        variable open_status : file_open_status;
        -- NOTE: the variable "stimulus" could mean clock_level or edge_transition, but it does not matter
        --       because to keep things consistent we check in addition against the variable "pos_edge".
        variable stimulus   : character;
        variable pos_edge            : boolean := false;
        variable initialized         : boolean := false;
    begin
        -- initialization?
        -- ###############
        if initialized = false then
            initialized := true;
            
            if (PROTOCOL_CLOCK = true) then
                report "simulated clock waiting to open for read on FIFO.";
            end if;
            -- open stimulus FIFO/named-pipe (created in external simulation app - VHDL is NOT able to create named pipes!)
            loop
                file_open(open_status, i_file, CLOCK_FILE_NAME,  read_mode);
                exit when open_status = open_ok;
            end loop;
            -- "block" until new line is sent (no CPU consumption!)
            -------------------------------------------------------
            read(i_file, stimulus);
            -- initialize hw_clock with external clock signal
            if stimulus = '1' then
                hw_clock <= '1';
                pos_edge := true;
                if (PROTOCOL_CLOCK = true) then
                    report "hw_clock initialized to 1";
                end if;
            else
                hw_clock <= '0';
                pos_edge := false;
                if (PROTOCOL_CLOCK = true) then
                    report "hw_clock initialized to 0";
                end if;
            end if;
            -- TODO: check if we need this here:
            wait for CLOCK_PERIOD / 2;
        -- check external clock signal
        -- ###########################
        else
            -- with this loop we avoid re-checking the variable "initialized" every time      
            loop
                -- "block" until a new line is sent over the FIFO (named pipe), no CPU consumption!
                -- WARNING!
                --         in VIVADO the complete simulation blocks. Processes are not concurrent in this particular case.
                --         For clock this is not problem because everything is driven by it.
                ----------------------------------------------------------------------------------------------------------
                read(i_file, stimulus);
                if (PROTOCOL_CLOCK = true) then
                    report "checking external clock..";
                end if;
                -- evaluate external clock signal
                if stimulus = '1' then               
                    -- as an error, the external clock signal may repeat/resend the same edge transition
                    -- therefore, we always check the current state of pos_edge
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
