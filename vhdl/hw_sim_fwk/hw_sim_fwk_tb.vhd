
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
use work.top_module;
library hw_sim_fwk;
use hw_sim_fwk.all;

entity hw_sim_fwk_tb is
end hw_sim_fwk_tb;

architecture arch of hw_sim_fwk_tb is
    -- constants for generic map:
    -- ##########################
    -- hw_sim_fwk_tb
    constant SIMULATE_BUTTON_IN_TESTBENCH : boolean := false; -- otherwise button simulated externally
    constant PROTOCOL                     : boolean := false; -- to report details
    constant FILE_PATH                    : string  := "/tmp/hw_sim_fwk/"; -- "C:/tmp/hw_sim_fwk/";       
    constant CLOCK_PERIOD                 : time    := 20 ns;
    -- modMCounter
    constant M                            : integer := 10;
    constant N                            : integer := 4;
    constant T                            : time    := CLOCK_PERIOD; -- 20 ns;
    -- hw_sim_fwk_reset
    constant RESET_FILE_NAME              : string  := FILE_PATH & "reset_high";
    constant PROTOCOL_RESET               : boolean := false; -- to report details of external hw reset simulation
    -- hw_sim_fwk_clock	 
    constant CLOCK_FILE_NAME              : string  := FILE_PATH & "clock_high";
    -- constant CLOCK_PERIOD_EXTERNAL : time := 1000000000 ns; -- 1 sec
    constant CLOCK_PERIOD_EXTERNAL        : time    := 100000000 ns; -- 100 ms = 0.1 sec
    -- constant CLOCK_PERIOD_EXTERNAL        : time    := 10000000 ns; -- 10 ms = 0.01 sec
    constant MAX_ELAPSED_CLOCK_PERIODS    : integer := (CLOCK_PERIOD_EXTERNAL / CLOCK_PERIOD) / 2;
    constant PROTOCOL_CLOCK               : boolean := false; -- to report details of external hw clock simulation
    -- hw_sim_fwk_digital_inputs
    constant NR_DIS                       : integer := 4; -- 64; -- 16; -- 2;
    constant DIS_FILE_NAME                : string  := FILE_PATH & "di_high";
    constant PROTOCOL_DIS                 : boolean := false; -- to report details of external hw digital inputs simulation
    -- hw_sim_fwk_switches
    constant NR_SWITCHES                  : integer := 10; -- 64; -- 16; -- 2;
    constant SWITCHES_FILE_NAME           : string  := FILE_PATH & "switch_high";
    constant PROTOCOL_SWITCHES            : boolean := false; -- to report details of external hw switches simulation
    -- hw_sim_fwk_buttons
    constant NR_BUTTONS                   : integer := 10; -- 4; -- 64; -- 1;
    constant BUTTONS_FILE_NAME            : string  := FILE_PATH & "button_high";
    constant PROTOCOL_BUTTONS             : boolean := false; -- to report details of external hw buttons simulation
    -- hw_sim_fwk_leds
    constant NR_LEDS                      : integer := 10; -- 4; -- 64; -- 16; -- 2;
    constant LEDS_ON_FILE_NAME            : string  := FILE_PATH & "led_on";
    constant LEDS_OFF_FILE_NAME           : string  := FILE_PATH & "led_off";
    constant PROTOCOL_LEDS                : boolean := false; -- to report details of external hw leds simulation
    -- hw_sim_fwk_digital_outputs
    constant NR_DOS                       : integer := 4; -- 64; -- 16; -- 2;
    constant DOS_HIGH_FILE_NAME           : string  := FILE_PATH & "do_high";
    constant DOS_LOW_FILE_NAME            : string  := FILE_PATH & "do_low";
    constant PROTOCOL_DOS                 : boolean := false; -- to report details of external hw digital outputs simulation
    -- signals:
    -- common signals
    -- ##############
    signal hw_clock_tb                    : std_logic; -- input, common for all modules
    signal reset_tb                       : std_logic; -- input, common for all modules
    -- ########
    -- modMCounter
    -- ###########
    -- Outputs
    signal complete_tick_tb               : std_logic;
    signal count_tb                       : std_logic_vector(N - 1 downto 0);
    -- dio
    -- ###
    --Inputs
    signal di_tb                          : std_logic_vector(NR_DIS - 1 downto 0);
    --Outputs
    signal do_tb                          : std_logic_vector(NR_DOS - 1 downto 0);
    -- switch leds
    -- ###########
    --Inputs
    signal switch_tb                      : std_logic_vector(NR_SWITCHES - 1 downto 0);
    signal button_tb                      : std_logic_vector(NR_BUTTONS - 1 downto 0);
    -- Note:
    -- button_tb_dummy is used when the button is simulated in the testbench, (see option in port map further below)
    -- the signals triggered by the external simulator go to nirvana in that case..
    signal button_tb_dummy                : std_logic_vector(NR_BUTTONS - 1 downto 0);
    --Outputs
    signal led_tb                         : std_logic_vector(NR_LEDS - 1 downto 0);
    -- further signals:
    -- ################
    -- stdin/stdout is a good alternative to implement a HW simulation framework driven externally
    -- but it is not supported by all simulation tools or needs special tricks and adaptations.
    -- here a test variable to get an integer from stdin:
    -- signal my_integer : integer;  -- see TODO further below     
begin
    -- asserts
    -- TODO: check this, right syntax? right place in code?
    --       use: string variable for report?
    -- msg : string(1 to 128) := "Unequal nr. of LEDs, switches, buttons = " & integer'image(NR_LEDS) & ", " & integer'image(NR_SWITCHES) & ", " & integer'image(NR_BUTTONS);
    assert ((NR_LEDS = NR_BUTTONS) and (NR_BUTTONS = NR_SWITCHES)) report ("Unequal nr. of LEDs, switches, buttons = " & integer'image(NR_LEDS) & ", " & integer'image(NR_SWITCHES) & ", " & integer'image(NR_BUTTONS)) severity failure;

    -- instantiate hw reset simulated externally
    -- #########################################
    hw_sim_fwk_reset_unit : entity hw_sim_fwk_reset
        generic map(
            FILE_PATH                 => FILE_PATH,
            RESET_FILE_NAME           => RESET_FILE_NAME,
            PROTOCOL_RESET            => PROTOCOL_RESET
        )
        port map(
            clock    => hw_clock_tb,
            hw_reset => reset_tb
        ); 
        
    -- instantiate hw clock simulated externally
    -- *** hw_clock from HW-simulation-framework drives clock of the synthesizable modules ***
    -- #######################################################################################
    hw_sim_fwk_clock_unit : entity hw_sim_fwk_clock
        generic map(
            FILE_PATH                 => FILE_PATH,
            CLOCK_FILE_NAME           => CLOCK_FILE_NAME,
            CLOCK_PERIOD              => CLOCK_PERIOD,
            MAX_ELAPSED_CLOCK_PERIODS => MAX_ELAPSED_CLOCK_PERIODS,
            PROTOCOL_CLOCK            => PROTOCOL_CLOCK
        )
        port map(
            hw_clock => hw_clock_tb
        );

    -- instantiate hw digital inputs simulated externally
    -- ##################################################
    hw_sim_fwk_digital_inputs_unit : entity hw_sim_fwk_digital_inputs
        generic map(
            NR_DIS             => NR_DIS,
            FILE_PATH          => FILE_PATH,
            DIS_FILE_NAME      => DIS_FILE_NAME,
            PROTOCOL_DIS       => PROTOCOL_DIS
        )
        port map(
            reset     => reset_tb,
            clock     => hw_clock_tb,
            hw_di     => di_tb
        );
        
    -- instantiate hw switches simulated externally
    -- ############################################
    hw_sim_fwk_switches_unit : entity hw_sim_fwk_switches
        generic map(
            NR_SWITCHES        => NR_SWITCHES,
            FILE_PATH          => FILE_PATH,
            SWITCHES_FILE_NAME => SWITCHES_FILE_NAME,
            PROTOCOL_SWITCHES  => PROTOCOL_SWITCHES
        )
        port map(
            reset     => reset_tb,
            clock     => hw_clock_tb,
            hw_switch => switch_tb
        );

    -- instantiate hw buttons, but button simulated in testbench
    -- so hw_button is discarded by setting dummy signal button_tb_dummy
    -- Note: the "else generate" construct is only supported in VHDL 1076-2008
    --       so we use a separate (and complementary) generate condition
    -- #######################################################################
    g_conditional_tb_button_simulation_1oo3 : if SIMULATE_BUTTON_IN_TESTBENCH = true generate
        hw_sim_fwk_buttons_unit : entity hw_sim_fwk_buttons
            generic map(
                NR_BUTTONS        => NR_BUTTONS, FILE_PATH => FILE_PATH,
                BUTTONS_FILE_NAME => BUTTONS_FILE_NAME,
                PROTOCOL_BUTTONS  => PROTOCOL_BUTTONS
            )
            port map(
                reset     => reset_tb,
                clock     => hw_clock_tb,
                hw_button => button_tb_dummy -- simulate button in testbench               
            );
    end generate g_conditional_tb_button_simulation_1oo3;

    -- instantiate hw buttons simulated externally
    -- ###########################################
    g_conditional_tb_button_simulation_2oo3 : if SIMULATE_BUTTON_IN_TESTBENCH = false generate -- else generate
        hw_sim_fwk_buttons_unit : entity hw_sim_fwk_buttons
            generic map(
                NR_BUTTONS        => NR_BUTTONS, FILE_PATH => FILE_PATH,
                BUTTONS_FILE_NAME => BUTTONS_FILE_NAME,
                PROTOCOL_BUTTONS  => PROTOCOL_BUTTONS
            )
            port map(
                reset     => reset_tb,
                clock     => hw_clock_tb,
                hw_button => button_tb  -- simulate button in external simulator               
            );
    end generate g_conditional_tb_button_simulation_2oo3;

    -- instantiate hw leds simulated externally
    -- ########################################
    hw_sim_fwk_leds_unit : entity hw_sim_fwk_leds
        generic map(
            NR_LEDS            => NR_LEDS,
            FILE_PATH          => FILE_PATH,
            LEDS_ON_FILE_NAME  => LEDS_ON_FILE_NAME,
            LEDS_OFF_FILE_NAME => LEDS_OFF_FILE_NAME,
            PROTOCOL_LEDS      => PROTOCOL_LEDS
        )
        port map(
            reset  => reset_tb,
            clock  => hw_clock_tb,
            hw_led => led_tb
        );
        
    -- instantiate hw digital outputs simulated externally
    -- ###################################################
    hw_sim_fwk_digital_outputs_unit : entity hw_sim_fwk_digital_outputs
        generic map(
            NR_DOS             => NR_DOS,
            FILE_PATH          => FILE_PATH,
            DOS_HIGH_FILE_NAME => DOS_HIGH_FILE_NAME,
            DOS_LOW_FILE_NAME  => DOS_LOW_FILE_NAME,
            PROTOCOL_DOS       => PROTOCOL_DOS
        )  
        port map(
            reset => reset_tb,
            clock => hw_clock_tb,
            hw_do => do_tb
        );
    
    -- instantiate top_module
    -- ######################
    top_module_unit : entity top_module
        generic map(
            -- modMCounter
            M           => M,
            N           => N,
            -- switch_leds
            NR_SWITCHES => NR_SWITCHES,
            NR_BUTTONS  => NR_BUTTONS,
            NR_LEDS     => NR_LEDS,
            -- dio
            NR_DIS      => NR_DIS,
            NR_DOS      => NR_DOS
        )
        port map(
            -- common
            reset_in          => reset_tb,
            clock_in          => hw_clock_tb,
            -- modMCounter
            complete_tick_out => complete_tick_tb,
            count_out         => count_tb,
            -- switch_leds
            switch_in         => switch_tb,
            button_in         => button_tb,
            led_out           => led_tb,
            -- dio
            di_in             => di_tb,
            do_out            => do_tb
        );

    -- report detection of rising and falling edges of clock
    -- #####################################################
    proc_status_hw_clock : process(hw_clock_tb)
    begin
        if PROTOCOL = true then         -- NOTE: use PROTOCOL_CLOCK alternatively..
            if rising_edge(hw_clock_tb) then
                report "simulated HW clock source with rising edge!";
            elsif falling_edge(hw_clock_tb) then
                report "simulated HW clock source with falling edge!";
            else
                report "simulated HW clock source neither rising nor falling edge!";
            end if;
            -- else
            -- finish/leave/stop process -> how? TODO: check this..		
        end if;
    end process proc_status_hw_clock;
    
    -- report detection of rising and falling edges of digital inputs
    -- ##############################################################
    proc_status_hw_di : process(di_tb)
    begin
        if PROTOCOL = true then         -- NOTE: use if PROTOCOL_DIS alternatively..
            if rising_edge(di_tb(0)) then
                report "simulated HW di(0) source with rising edge!";
            elsif falling_edge(di_tb(0)) then
                report "simulated HW di(0) source with falling edge!";
            else
                report "simulated HW di(0) source neither rising nor falling edge!";
            end if;
            -- else
            -- finish/leave/stop process -> how? TODO: check this..		
        end if;
    end process proc_status_hw_di;

    -- report detection of rising and falling edges of switches
    -- ########################################################
    proc_status_hw_switch : process(switch_tb)
    begin
        if PROTOCOL = true then         -- NOTE: use if PROTOCOL_SWITCHES alternatively..
            if rising_edge(switch_tb(0)) then
                report "simulated HW switch(0) source with rising edge!";
            elsif falling_edge(switch_tb(0)) then
                report "simulated HW switch(0) source with falling edge!";
            else
                report "simulated HW switch(0) source neither rising nor falling edge!";
            end if;
            -- else
            -- finish/leave/stop process -> how? TODO: check this..		
        end if;
    end process proc_status_hw_switch;

    -- report detection of rising and falling edges of buttons
    -- #######################################################
    proc_status_hw_buttons : process(button_tb)
    begin
        if PROTOCOL = true then         -- NOTE: use if PROTOCOL_BUTTONS alternatively..
            if rising_edge(button_tb(0)) then
                report "simulated HW button 0 source with rising edge!";
            elsif falling_edge(button_tb(0)) then
                report "simulated HW button 0 source with falling edge!";
            else
                report "simulated HW button 0 source neither rising nor falling edge!";
            end if;
            -- else
            -- finish/leave/stop process -> how? TODO: check this..		
        end if;
    end process proc_status_hw_buttons;

    -- report detection of rising and falling edges of leds
    -- ####################################################
    proc_status_hw_leds : process(led_tb)
    begin
        if PROTOCOL = true then         -- NOTE: use if PROTOCOL_LED alternatively..
            if rising_edge(led_tb(0)) then
                report "simulated HW led 0 source with rising edge!";
            elsif falling_edge(led_tb(0)) then
                report "simulated HW led 0 source with falling edge!";
            else
                report "simulated HW led 0 source neither rising nor falling edge!";
            end if;
            -- else
            -- finish/leave/stop process -> how? TODO: check this..		
        end if;
    end process proc_status_hw_leds;
    
    -- report detection of rising and falling edges of digital outputs
    -- ###############################################################
    proc_status_hw_dos : process(do_tb)
    begin
        if PROTOCOL = true then         -- NOTE: use if PROTOCOL_DO alternatively..
            if rising_edge(do_tb(0)) then
                report "simulated HW digital output 0 source with rising edge!";
            elsif falling_edge(do_tb(0)) then
                report "simulated HW digital output 0 source with falling edge!";
            else
                report "simulated HW digital output 0 source neither rising nor falling edge!";
            end if;
            -- else
            -- finish/leave/stop process -> how? TODO: check this..		
        end if;
    end process proc_status_hw_dos;

    -- short test on stdin and stdout (stdin NOK, see TODO)
    -- ####################################################
    proc_std_input_output : process(reset_tb)
        variable my_line : line;
        -- variable my_integer_var : integer;  -- see TODO below
    begin
        write(my_line, 16);
        writeline(output, my_line);
        -- TODO: 
        --       check how to input from stdin to iSim,
        --       it works fine when using GHDL.
        --       readline() blocks until user input ended with return hit.
        -- readline(input, my_line);
        -- read(my_line, my_integer_var);
        -- my_integer <= my_integer_var;		  
    end process proc_std_input_output;

    -- active test-bench tests, parallel to external simulation
    -- when button_tb_dummy is used, then button_tb is set in this process
    -- instead of being triggered by the external simulator.
    -- ###################################################################
    g_conditional_tb_button_simulation_3oo3 : if SIMULATE_BUTTON_IN_TESTBENCH = true generate
        proc_testbench_main : process(hw_clock_tb, reset_tb)
            variable clock_periods : integer := 0;
        begin
            if reset_tb = '1' then
                button_tb(0) <= '0';
                if true then            -- PROTOCOL = true then
                    report "initialized button 1 to ZERO";
                end if;
            elsif rising_edge(hw_clock_tb) then
                clock_periods := clock_periods + 1;
                if clock_periods = 8 then -- Note: hardcoded value for test.
                    -- reset_tb <= '1';
                    button_tb(0)  <= not button_tb(0); -- '1';
                    clock_periods := 0;
                    if true then        -- PROTOCOL = true then
                        report "toggled button 1";
                    end if;
                end if;
            end if;
        end process proc_testbench_main;
    end generate g_conditional_tb_button_simulation_3oo3;

    -- keep on counting from start
    -- NOTE: commented as this is done in the external HW simulation
    -- #############################################################  
    -- reset_tb <= '1', '0' after T / 2;   --reset long enough!!
end arch;


